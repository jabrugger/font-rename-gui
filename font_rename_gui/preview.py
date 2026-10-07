"""Read-only presentation of engine output; filters never alter processing."""
import ast
import json
import re
from pathlib import Path
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter, QPen
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QModelIndex
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTableView, QPlainTextEdit, QSplitter, QHeaderView)

TEXT = {
 'es': {'rename':'Renombrar', 'internal':'Limpiar nombre interno', 'duplicate':'Eliminar duplicado',
        'extract':'Extraer colección', 'error':'Error', 'warning':'Advertencia', 'all':'Todas las acciones',
        'search':'Buscar por nombre o carpeta…', 'headers':['Estado','Acción','Nombre actual','Nombre propuesto'],
        'folder':'Carpeta', 'detail':'Seleccioná un archivo para ver sus detalles.', 'keep':'Conservar',
        'hint':'Los filtros solo cambian la vista. Se aplicará el resultado completo de la vista previa.',
        'summary':'Archivos: {files} · Renombrados: {rename} · Cambios internos: {internal} · Duplicados: {duplicate} · Errores: {error} · Advertencias: {warning}',
        'stale':'Configuración modificada: generá una nueva vista previa antes de aplicar.'},
 'en': {'rename':'Rename', 'internal':'Clean internal name', 'duplicate':'Remove duplicate',
        'extract':'Extract collection', 'error':'Error', 'warning':'Warning', 'all':'All actions',
        'search':'Search by name or folder…', 'headers':['Status','Action','Current name','Proposed name'],
        'folder':'Folder', 'detail':'Select a file to inspect its details.', 'keep':'Keep',
        'hint':'Filters only change the view. Applying processes the complete preview result.',
        'summary':'{files} files · {rename} renamed · {internal} internal edits · {duplicate} duplicates · {error} errors · {warning} warnings',
        'stale':'Configuration changed: generate a new preview before applying.'}
}


def unquote(value):
    try:
        result=ast.literal_eval(value)
        return result if isinstance(result,str) else value
    except (ValueError,SyntaxError):
        return value


class PreviewModel(QAbstractTableModel):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner=owner
        self.icons={}
        for status,color in [('done','#7dd99b'),('error','#ef8d88')]:
            pixmap=QPixmap(18,18); pixmap.fill(Qt.GlobalColor.transparent)
            painter=QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(color),2.4))
            if status=='done':
                painter.drawLine(3,9,7,13); painter.drawLine(7,13,15,4)
            else:
                painter.drawLine(4,4,14,14); painter.drawLine(14,4,4,14)
            painter.end(); self.icons[status]=QIcon(pixmap)
    def rowCount(self,parent=None): return len(self.owner.rows)
    def columnCount(self,parent=None): return 4
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if orientation==Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return TEXT[self.owner.language]['headers'][section]
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row=self.owner.rows[index.row()]
        if role==Qt.ItemDataRole.DecorationRole and index.column()==0:
            return self.icons.get(row.get('status'))
        if role==Qt.ItemDataRole.ForegroundRole and index.column()==0:
            return QColor({'done':'#7dd99b','error':'#ef8d88','processing':'#e2b97b'}.get(row.get('status'),'#a2acba'))
        if role==Qt.ItemDataRole.ToolTipRole: return row['folder']
        if role==Qt.ItemDataRole.DisplayRole:
            return [self.owner.status_text(row),', '.join(TEXT[self.owner.language][a] for a in row['actions']),row['current'],row['new']][index.column()]


class PreviewFilter(QSortFilterProxyModel):
    def filterAcceptsRow(self,index,parent):
        owner=self.sourceModel().owner
        row=owner.rows[index]
        action=owner.action.currentData()
        query=owner.search.text().casefold().strip()
        return (not action or action in row['actions']) and (not query or query in (' '.join([row['current'],row['new'],row['folder']])).casefold())


class PreviewWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.language='es'; self.rows=[]; self.lookup={}; self.block=[]; self.applying=False
        layout=QVBoxLayout(self)
        self.summary=QLabel(); self.summary.setWordWrap(True); layout.addWidget(self.summary)
        controls=QHBoxLayout(); self.search=QLineEdit(); self.action=QComboBox()
        controls.addWidget(self.search,1); controls.addWidget(self.action); layout.addLayout(controls)
        self.model=PreviewModel(self); self.proxy=PreviewFilter(self); self.proxy.setSourceModel(self.model)
        self.table=QTableView(); self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().resizeSection(0,140)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().resizeSection(1,260)
        self.table.sortByColumn(2,Qt.SortOrder.AscendingOrder)
        self.table.verticalHeader().hide()
        self.details=QPlainTextEdit(); self.details.setReadOnly(True); self.details.setMaximumBlockCount(160); self.details.setMinimumHeight(200)
        self.detail_caption=QLabel()
        self.detail_caption.setTextFormat(Qt.TextFormat.PlainText)
        self.detail_caption.setObjectName('detailCaption')
        self.detail_caption.setWordWrap(True)
        detail_panel=QWidget()
        detail_layout=QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0,0,0,0)
        detail_layout.addWidget(self.detail_caption)
        detail_layout.addWidget(self.details,1)
        self.splitter=QSplitter(Qt.Orientation.Vertical)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(detail_panel)
        self.splitter.setSizes([270,290])
        layout.addWidget(self.splitter,1)
        self.hint=QLabel(); self.hint.setWordWrap(True); layout.addWidget(self.hint)
        self.search.textChanged.connect(self.filter_changed)
        self.action.currentIndexChanged.connect(self.filter_changed)
        self.table.selectionModel().selectionChanged.connect(lambda *args:self.show_detail(self.selected_index()))
        self.set_language('es')

    def set_language(self,language):
        self.language=language; text=TEXT[language]; selected=self.action.currentData()
        self.action.blockSignals(True); self.action.clear(); self.action.addItem(text['all'],'')
        for key in ['rename','internal','duplicate','extract','error','warning']: self.action.addItem(text[key],key)
        self.action.setCurrentIndex(max(0,self.action.findData(selected))); self.action.blockSignals(False)
        self.search.setPlaceholderText(text['search']); self.details.setPlaceholderText(text['detail'])
        self.splitter.handle(1).setToolTip('Arrastrá para ajustar la altura de la lista y los detalles.' if language=='es' else 'Drag to resize the list and details.')
        self.hint.setText(text['hint']); self.refresh(); self.show_detail(self.selected_index())

    def reset(self):
        self.rows=[]; self.lookup={}; self.block=[]; self.applying=False; self.details.clear(); self.refresh()

    def stale(self): self.hint.setText(TEXT[self.language]['stale'])

    def selected_index(self):
        selected=self.table.selectionModel().selectedRows()
        return selected[0] if selected else QModelIndex()

    def select_visible(self,source_row=None):
        index=self.proxy.mapFromSource(self.model.index(source_row,0)) if source_row is not None else QModelIndex()
        if not index.isValid() and self.proxy.rowCount(): index=self.proxy.index(0,0)
        if index.isValid():
            self.table.setCurrentIndex(index)
            self.table.selectRow(index.row())
        else:
            self.table.clearSelection()
        self.show_detail(self.selected_index())

    def filter_changed(self,*args):
        source=self.proxy.mapToSource(self.selected_index())
        preferred=source.row() if source.isValid() else None
        self.proxy.invalidate()
        self.select_visible(preferred)

    def refresh(self):
        source=self.proxy.mapToSource(self.selected_index())
        preferred=source.row() if source.isValid() and source.row()<len(self.rows) else None
        self.model.beginResetModel(); self.model.endResetModel()
        self.select_visible(preferred)
        counts={key:sum(key in r['actions'] for r in self.rows) for key in ['rename','internal','duplicate','error','warning']}
        self.summary.setText(TEXT[self.language]['summary'].format(files=len(self.rows),**counts))

    def consume(self,text):
        for line in text.splitlines():
            header=line in ('RENAME:','INTERNAL:','DUPLICATE:','EXTRACT:') or line.startswith(('ERROR (','WARNING ('))
            boundary=bool(re.match(r'\d+ changes,|\d+ fonts with internal|=== |EXIT STATUS:|PREVIEW:|APPLY$|LOG:|PHASE:',line))
            if line.startswith('GUI_EVENT: '):
                self.flush()
                try: self.apply_event(json.loads(line[11:]))
                except (ValueError,KeyError): pass
                continue
            if header or boundary: self.flush()
            if header: self.block=[line]
            elif self.block and not boundary: self.block.append(line)
        self.refresh()

    def finish(self): self.flush(); self.refresh()

    def flush(self):
        if not self.block: return
        lines=self.block; self.block=[]; header=lines[0]
        fields={}
        for line in lines[1:]:
            if line.startswith('  ') and not line.startswith('    ') and ': ' in line:
                k,v=line.strip().split(': ',1); fields.setdefault(k,v)
        action={'RENAME:':'rename','INTERNAL:':'internal','DUPLICATE:':'duplicate','EXTRACT:':'extract'}.get(header)
        if not action: action='error' if header.startswith('ERROR') else 'warning'
        folder=fields.get('FOLDER',''); current=unquote(fields.get('CURRENT',fields.get('FILE',fields.get('COLLECTION',''))))
        if action in ('error','warning'):
            path=fields.get('FILE','')
            if not path and '): ' in header: path=header.split('): ',1)[1].split(': ',1)[0]
            if path: current=Path(path).name; folder=str(Path(path).parent)
            else: current=header
        new=unquote(fields.get('NEW',current))
        if action=='duplicate': new=''; fields['KEEP']=fields.get('KEEP','')
        key=(folder.casefold(),current.casefold())
        index=self.lookup.get(key)
        if index is None:
            index=len(self.rows); self.rows.append({'actions':[],'current':current,'new':new,'folder':folder,'blocks':[],'status':'pending' if self.applying else 'preview','results':{}})
        row=self.rows[index]
        if action not in row['actions']: row['actions'].append(action)
        if action=='error': row['status']='error'
        elif action=='warning' and row['status']=='preview': row['status']='warning'
        if action=='rename': row['new']=new
        if action=='extract':
            targets=row.setdefault('extracted',[])
            if new not in targets: targets.append(new)
            row['new']='; '.join(targets)
        row['blocks'].append('\n'.join(lines)[:12000])
        self.lookup[key]=index
        if new and action!='extract': self.lookup[(folder.casefold(),new.casefold())]=index

    def status_text(self,row):
        status=row.get('status','preview')
        labels={'es':{'preview':'Por aplicar','pending':'Pendiente','processing':'Procesando','done':'Completado','error':'Error','warning':'Advertencia','unchanged':'Sin cambios','not_processed':'No procesado'},
                'en':{'preview':'Proposed','pending':'Pending','processing':'Processing','done':'Completed','error':'Error','warning':'Warning','unchanged':'Unchanged','not_processed':'Not processed'}}
        return labels[self.language].get(status,status)

    def begin_apply(self):
        self.applying=True
        for row in self.rows:
            row['results']={}
            row['status']='pending' if any(a in row['actions'] for a in ['rename','duplicate','extract','internal']) else row.get('status','warning')
        self.refresh()

    def apply_event(self,event):
        path=Path(event['path']); key=(str(path.parent).casefold(),path.name.casefold())
        index=self.lookup.get(key)
        if index is None: return
        row=self.rows[index]
        expected={'internal' if a=='internal' else 'file' for a in row['actions'] if a in ['rename','duplicate','extract','internal']}
        phase,status=event['phase'],event['status']
        if phase not in expected: return
        if status=='processing':
            if row['status']!='error': row['status']='processing'
        else:
            if row['results'].get(phase)=='error': status='error'
            row['results'][phase]=status
            if 'error' in row['results'].values(): row['status']='error'
            elif 'not_processed' in row['results'].values(): row['status']='not_processed'
            elif expected.issubset(row['results']): row['status']='done' if 'done' in row['results'].values() else 'unchanged'
            else: row['status']='pending'

    def finish_apply(self):
        self.finish()
        for row in self.rows:
            if row['status'] in ('processing','pending'): row['status']='not_processed'
        self.refresh()

    def show_detail(self,index,*args):
        source=self.proxy.mapToSource(index)
        if not index.isValid() or not source.isValid() or not 0<=source.row()<len(self.rows):
            self.details.clear()
            self.detail_caption.setText(TEXT[self.language]['detail'])
            return
        row=self.rows[source.row()]; text=TEXT[self.language]
        self.detail_caption.setText(('Detalle de: ' if self.language=='es' else 'Details for: ')+row['current'])
        results='\n'.join(('Nombres internos' if phase=='internal' else 'Archivo')+': '+self.status_text({'status':status}) for phase,status in row['results'].items()) if self.language=='es' else '\n'.join(phase+': '+self.status_text({'status':status}) for phase,status in row['results'].items())
        detail=f"{text['folder']}: {row['folder']}\n{results}\n\n"+'\n\n'.join(row['blocks'])
        if self.language=='es':
            for old,new in [('CURRENT:','ACTUAL:'),('NEW:','NUEVO:'),('FOLDER:','CARPETA:'),('FILE:','ARCHIVO:'),('KEEP:','CONSERVAR:'),('NAME ID ','CAMPO DE NOMBRE '),('COLLECTION:','COLECCIÓN:'),('RENAME:','RENOMBRAR:'),('INTERNAL:','NOMBRES INTERNOS:'),('DUPLICATE:','DUPLICADO:'),('EXTRACT:','EXTRAER:')]:
                detail=re.sub(r'(?m)^(\s*)'+re.escape(old),lambda m:m[1]+new,detail)
        self.details.setPlainText(detail)
