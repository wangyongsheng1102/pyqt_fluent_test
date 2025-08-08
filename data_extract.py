import os.path

import pandas as pd
import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QTableWidgetItem, QSizePolicy, \
    QHeaderView, QTabWidget, QPushButton, QTableWidget, QFileDialog, QStyledItemDelegate, QApplication
from qfluentwidgets import ScrollArea, ExpandLayout, isDarkTheme, setTheme, Theme, setThemeColor, PushButton, \
    FluentIcon, HeaderCardWidget, PrimaryPushButton, TransparentPushButton, LineEdit, TextEdit, TableWidget, InfoBar, \
    MessageBox, ToggleToolButton, TransparentToolButton, StateToolTip, SwitchButton

from datetime import datetime

from config import cfg

BASE = cfg.url_base.value


class DataExtractInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("DataExtract-Interface")
        self.layout = QVBoxLayout()

        self.headerButtonCard = HeaderButtonCard()
        self.layout.addWidget(self.headerButtonCard)
        self.headerTextCard = HeaderTextCard()
        self.headerTextCard.setDisabled(True)
        self.layout.addWidget(self.headerTextCard)
        self.bottomTableCard = BottomTableCard()
        self.bottomTableCard.setDisabled(True)
        self.layout.addWidget(self.bottomTableCard)

        self.setLayout(self.layout)
        self.setFocusPolicy(Qt.StrongFocus)


class HeaderButtonCard(HeaderCardWidget):

    def __init__(self):
        super().__init__()
        self.setTitle(self.tr("チェック"))
        self.setFixedHeight(135)

        self.stackedWidget = QStackedWidget(self)

        self.contentLayout = QVBoxLayout()
        self.buttonsLayout = QHBoxLayout()

        self.checkButton = PrimaryPushButton(FluentIcon.VIEW, self.tr("接続チェック"))
        self.checkButton.setFixedWidth(150)
        self.checkButton.clicked.connect(self.checkButtonClick)
        # self.copyButton.clicked.connect(self.copyResult)
        # self.buttonLayout.addWidget(self.copyButton, 0, Qt.AlignCenter)
        self.buttonsLayout.addWidget(self.checkButton)

        self.contentLayout.addLayout(self.buttonsLayout)
        # self.contentLayout.addWidget(self.stackedWidget)

        self.viewLayout.addLayout(self.contentLayout)

    def checkButtonClick(self):
        try:
            r = requests.get(f"{BASE}/ping")
            r.raise_for_status()
            if r.status_code == 200:
                InfoBar.success(
                    title=self.tr("接続"),
                    content=self.tr("接続成功。"),
                    parent=self.parent(),
                    duration=2500
                ).show()
                self.parent().headerTextCard.setDisabled(False)
                self.parent().bottomTableCard.setDisabled(False)
            else:
                InfoBar.warning(
                    title=self.tr("接続"),
                    content=self.tr(f"接続失敗、レスポンスコード「{r.status_code}」"),
                    parent=self.parent(),
                    duration=2500
                ).show()
        except Exception as e:
            self.showMessageDialog("接続", "接続失敗、サービスをチェックしてください。\n" + str(e))

    def showMessageDialog(self, title_par, content_par):
        title = self.tr(title_par)
        content = self.tr(content_par)
        w = MessageBox(title, content, self.window())
        w.setContentCopyable(True)
        if w.exec():
            print('Yes button is pressed')
        else:
            print('Cancel button is pressed')


class HeaderTextCard(HeaderCardWidget):

    def __init__(self):
        super().__init__()
        self.setTitle(self.tr("出力"))
        self.stackedWidget = QStackedWidget(self)
        self.setFixedHeight(180)

        self.contentLayout = QVBoxLayout()
        self.textLayout = QHBoxLayout()

        self.openButton = TransparentPushButton(self.tr('出力フォルダ'), self, FluentIcon.BOOK_SHELF)
        self.openButton.setFixedWidth(150)
        self.openButton.clicked.connect(self.openButtonClick)

        self.lineEdit = LineEdit(self)
        self.lineEdit.setText(self.tr(''))
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.textChanged.connect(self.lineEditChanged)

        self.textLayout.addWidget(self.openButton)
        self.textLayout.addWidget(self.lineEdit)

        self.executeButton = PrimaryPushButton(self.tr('実行'), self, FluentIcon.BOOK_SHELF)
        self.executeButton.clicked.connect(self.executeButtonClick)
        self.targetButton = TransparentToolButton(FluentIcon.FOLDER, self)
        self.targetButton.clicked.connect(self.targetButtonClick)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.executeButton)
        self.buttonLayout.addWidget(self.targetButton)

        self.contentLayout.addLayout(self.textLayout)
        self.contentLayout.addLayout(self.buttonLayout)
        # self.contentLayout.addWidget(self.stackedWidget)

        self.viewLayout.addLayout(self.contentLayout)

    def openButtonClick(self):
        # 打开系统目录选择对话框
        try:
            options = QFileDialog.Options()
            if self.lineEdit.text() is not None and self.lineEdit.text() != "":
                open_path = self.lineEdit.text()
            else:
                open_path = cfg.output_dir.value
            folder_path = QFileDialog.getExistingDirectory(self, "フォルダ選択",
                                                           directory=open_path,
                                                           options=options)
            if folder_path:
                self.lineEdit.setText(folder_path)
                cfg.set(cfg.output_dir, folder_path)
        except Exception as e:
            InfoBar.warning(
                title=self.tr("フォルダ"),
                content=self.tr(f"フォルダ誤り。\n" + str(e)),
                parent=self.parent(),
                duration=2500
            ).show()

    def lineEditChanged(self):
        if os.path.exists(self.lineEdit.text().strip()) is False:
            InfoBar.warning(
                title=self.tr("フォルダ"),
                content=self.tr(f"入力したフォルダが不存在であり、チェックしてください。"),
                parent=self.parent(),
                duration=2500
            ).show()

    def executeButtonClick(self):
        self.parent().bottomTableCard.tableFrame.clear_all_rows()
        self.stateTooltip = StateToolTip(
            self.tr('テーブル検索中'), self.tr('少々お待ちください。'), self.window())
        self.stateTooltip.setToolTipDuration(5000)
        # self.sender().setText(self.tr('Hide StateToolTip'))
        self.stateTooltip.move(self.stateTooltip.getSuitablePos())
        self.stateTooltip.show()
        QApplication.processEvents()
        try:
            r = requests.get(f"{BASE}/tables")
            r.raise_for_status()
            if r.status_code == 200:
                InfoBar.success(
                    title=self.tr("テーブル"),
                    content=self.tr("テーブル取得成功。"),
                    parent=self.parent(),
                    duration=2500
                ).show()

                for index, line in enumerate(r.json()):
                    schema = line['TABLE_SCHEMA']
                    table = line['TABLE_NAME']
                    s = requests.get(f"{BASE}/table/{schema}/{table}/primary-keys")
                    if len(s.json()) == 0:
                        primary_keys = "なし"
                    else:
                        primary_keys = ""
                        for keys in s.json():
                            primary_keys += "[ " + keys['COLUMN_NAME'] + " ] "

                    # t = requests.get(f"{BASE}/table/{schema}/{table}/schema")
                    # table_columns = ""
                    # for col in t.json():
                    #     table_columns += str(col) + "\n"
                    self.parent().bottomTableCard.tableFrame.add_row([schema, table, primary_keys, ""])
            else:
                InfoBar.warning(
                    title=self.tr("テーブル"),
                    content=self.tr(f"接続失敗、レスポンスコード「{r.status_code}」"),
                    parent=self.parent(),
                    duration=2500
                ).show()
        except Exception as e:
            self.showMessageDialog("テーブル", "接続失敗、サービスをチェックしてください。\n" + str(e))

        self.stateTooltip.setContent(
            self.tr('検索終了!') + ' 😆')
        # self.sender().setText(self.tr('Show StateToolTip'))
        self.stateTooltip.setState(True)
        self.stateTooltip = None
        self.parent().bottomTableCard.tableFrame.scrollToTop()

    def targetButtonClick(self):
        try:
            if self.lineEdit.text().strip() is None or self.lineEdit.text().strip() == "":
                os.startfile(cfg.output_dir.value)
            else:
                os.startfile(self.lineEdit.text().strip())
        except Exception as e:
            InfoBar.warning(
                title=self.tr("フォルダ"),
                content=self.tr(f"フォルダを開くことができません。\n" + str(e)),
                parent=self.parent(),
                duration=2500
            ).show()

    def showMessageDialog(self, title_par, content_par):
        title = self.tr(title_par)
        content = self.tr(content_par)
        w = MessageBox(title, content, self.window())
        w.setContentCopyable(True)
        if w.exec():
            print('Yes button is pressed')
        else:
            print('Cancel button is pressed')


class BottomTableCard(HeaderCardWidget):

    def __init__(self):
        super().__init__()
        self.setTitle(self.tr("結果"))
        self.stackedWidget = QStackedWidget(self)

        self.contentLayout = QVBoxLayout()
        self.textEditLayout = QVBoxLayout()

        self.tableFrame = TableFrame(self)
        # self.tableFrame.setSizePolicy(
        #     self.tableFrame.sizePolicy().Policy.Expanding,
        #     self.tableFrame.sizePolicy().Policy.Expanding
        # )
        # self.tableFrame.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.textEditLayout.addWidget(self.tableFrame)

        self.buttonLayout = QVBoxLayout()
        self.exportButton = PrimaryPushButton(self.tr('一括エクスポート'), self, FluentIcon.IMAGE_EXPORT)
        self.exportButton.clicked.connect(self.exportButtonClick)
        self.buttonLayout.addWidget(self.exportButton)

        self.contentLayout.addLayout(self.textEditLayout)
        self.contentLayout.addLayout(self.buttonLayout)
        # self.contentLayout.addWidget(self.stackedWidget)

        self.viewLayout.addLayout(self.contentLayout)

    def exportButtonClick(self):
        self.stateTooltip = StateToolTip(
            self.tr('CSVファイル出力'), self.tr('少々お待ちください。'), self.window())
        self.stateTooltip.setToolTipDuration(5000)
        # self.sender().setText(self.tr('Hide StateToolTip'))
        self.stateTooltip.move(self.stateTooltip.getSuitablePos())
        self.stateTooltip.show()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        if self.parent().headerTextCard.lineEdit.text().strip() is None or \
                self.parent().headerTextCard.lineEdit.text().strip() == "":
            save_path = os.path.join(cfg.output_dir.value, "データベース-CSVファイル-" + timestamp)
        else:
            save_path = os.path.join(self.parent().headerTextCard.lineEdit.text().strip(), "データベースCSVファイル" + timestamp)

        os.makedirs(save_path)

        for row in range(self.tableFrame.rowCount()):
            for column in range(self.tableFrame.columnCount()):
                if column == 0:
                    schema = self.tableFrame.item(row, column).text()
                if column == 1:
                    url = self.tableFrame.item(row, column).data(Qt.UserRole)
                    table = self.tableFrame.item(row, column).text()
                    if url:
                        try:
                            r = requests.get(url)
                            r.raise_for_status()
                            if r.status_code == 200:
                                table_data = r.json()
                                rows = table_data["rows"]
                                if len(rows) == 0:
                                    continue
                                df = pd.DataFrame(rows)
                                csv_path = os.path.join(save_path, f"{schema}-{table}.csv")
                                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                                # InfoBar.success(
                                #     title=self.tr("テーブル"),
                                #     content=self.tr(f"テーブルデータ取得成功。\n{csv_path}"),
                                #     parent=self.parent(),
                                #     duration=3000
                                # ).show()
                            else:
                                pass
                                # InfoBar.warning(
                                #     title=self.tr("テーブル"),
                                #     content=self.tr(f"接続失敗、レスポンスコード「{r.status_code}」"),
                                #     parent=self.parent(),
                                #     duration=2500
                                # ).show()
                        except Exception as e:
                            InfoBar.warning(
                                title=self.tr("テーブル"),
                                content=self.tr(f"{e}"),
                                parent=self.parent(),
                                duration=2500
                            ).show()
                    continue

        self.stateTooltip.setContent(
            self.tr('出力終了!') + ' 😆')
        # self.sender().setText(self.tr('Show StateToolTip'))
        self.stateTooltip.setState(True)
        self.stateTooltip.setToolTipDuration(5000)
        self.stateTooltip = None


class LinkDelegate(QStyledItemDelegate):
    # def paint(self, painter, option, index):
    #     # 先调用基类的 paint 方法，保留原有样式
    #     super().paint(painter, option, index)
    #     # 获取原始文本
    #     text = index.data(Qt.DisplayRole)
    #
    #     # 设置字体为加粗 + 下划线
    #     font = painter.font()
    #     font.setBold(True)  # 加粗
    #     font.setUnderline(True)  # 下划线
    #
    #     # 保存当前绘图状态
    #     painter.save()
    #
    #     # 应用新字体
    #     painter.setFont(font)
    #
    #     # 绘制文本（左对齐 + 垂直居中）
    #     painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, text)
    #
    #     # 恢复绘图状态
    #     painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.MouseButtonPress:
            # 获取 URL
            url = index.data(Qt.UserRole)
            table = index.data(Qt.EditRole)
            if url:
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    if r.status_code == 200:
                        table_data = r.json()
                        rows = table_data["rows"]
                        if len(rows) == 0:
                            InfoBar.warning(
                                title=self.tr("テーブル"),
                                content=self.tr(f"テーブルのデータが０件です"),
                                parent=self.parent(),
                                duration=2500
                            ).show()
                            return True
                        df = pd.DataFrame(rows)
                        csv_path = os.path.join(cfg.output_dir.value, f"{table}.csv")
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        InfoBar.success(
                            title=self.tr("テーブル"),
                            content=self.tr(f"テーブルデータ取得成功。\n{csv_path}"),
                            parent=self.parent(),
                            duration=3000
                        ).show()
                        # for index, line in enumerate(r.json()):
                        #     self.parent().bottomTableCard.tableFrame.add_row([line['TABLE_SCHEMA'], line['TABLE_NAME']])
                    else:
                        InfoBar.warning(
                            title=self.tr("テーブル"),
                            content=self.tr(f"接続失敗、レスポンスコード「{r.status_code}」"),
                            parent=self.parent(),
                            duration=2500
                        ).show()
                except Exception as e:
                    InfoBar.warning(
                        title=self.tr("テーブル"),
                        content=self.tr(f"{e}"),
                        parent=self.parent(),
                        duration=2500
                    ).show()
                    return False

            return True  # ✅ 重要！必须返回 True，表示事件已处理
        return super().editorEvent(event, model, option, index)


class TableFrame(TableWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.verticalHeader().hide()
        self.setBorderRadius(5)
        self.setBorderVisible(True)
        self.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # self.setSortingEnabled(True)

        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            self.tr('スキーマ'),
            self.tr('テーブル'),
            self.tr('主キー'),
            self.tr('テーブル構造'),
            self.tr('✅')
        ])
        self.cellClicked.connect(self.handle_cell_click)

        self.resizeColumnsToContents()
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.sizeAdjustPolicy()
        self.setContentsMargins(0, 0, 0, 0)
        QApplication.processEvents()

    def handle_cell_click(self, row, col):
        if col == 1:
            item = self.item(row, col)
            # 获取 URL
            url = item.data(Qt.UserRole)
            # table = index.data(Qt.EditRole)
            table = item.text()
            schema = self.item(row, col - 1).text()
            if url:
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    if r.status_code == 200:
                        table_data = r.json()
                        rows = table_data["rows"]
                        if len(rows) == 0:
                            InfoBar.warning(
                                title=self.tr("テーブル"),
                                content=self.tr(f"テーブルのデータが０件です"),
                                parent=self.parent(),
                                duration=2500
                            ).show()
                            return
                        df = pd.DataFrame(rows)
                        csv_path = os.path.join(cfg.output_dir.value, f"{schema}-{table}.csv")
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        InfoBar.success(
                            title=self.tr("テーブル"),
                            content=self.tr(f"テーブルデータ取得成功。\n{csv_path}"),
                            parent=self.parent(),
                            duration=3000
                        ).show()
                    else:
                        InfoBar.warning(
                            title=self.tr("テーブル"),
                            content=self.tr(f"接続失敗、レスポンスコード「{r.status_code}」"),
                            parent=self.parent(),
                            duration=2500
                        ).show()
                except Exception as e:
                    InfoBar.warning(
                        title=self.tr("テーブル"),
                        content=self.tr(f"{e}"),
                        parent=self.parent(),
                        duration=2500
                    ).show()

    ### 新增方法：添加行
    def add_row(self, data: list):
        """
        添加一行数据到表格末尾
        :param data: 包含两个元素的列表 [schema, table]
        """
        if len(data) != 4:
            raise ValueError("Data must contain exactly two elements for schema and table.")

        row_count = self.rowCount()
        self.insertRow(row_count)

        # delegate = LinkDelegate(self)
        # self.setItemDelegateForColumn(1, delegate)

        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            if col == 0:
                schema = value
            if col == 1:
                font = item.font()
                # font.setBold(True)
                font.setUnderline(True)

                item.setFont(font)
                item.setData(Qt.EditRole, value)
                item.setData(Qt.UserRole, f"{BASE}/table/{schema}/{value}/full")
            self.setItem(row_count, col, item)

        # switchButton = SwitchButton()
        # switchButton.checkedChanged.connect(lambda checked, row=row_count: self.onSwitchCheckedChanged(row, checked))
        # # switchButton.clicked.connect(lambda checked, row=row_count: self.onButtonClick(row))
        # self.setCellWidget(row_count, 4, switchButton)

        self.resizeColumnsToContents()  # 自动调整列宽

    def onSwitchCheckedChanged(self, row, is_checked):
        print(f'Button clicked in row {row}')
        if is_checked:
            item = self.item(row, 1)
            url = item.data(Qt.UserRole)
            table = item.text()
            schema = self.item(row, 0).text()
            url = f"{BASE}/table/{schema}/{table}/schema"
            t = requests.get(url)
            table_columns = ""
            for col in t.json():
                table_columns += str(col) + "\n"
            self.item(row, 3).setText(table_columns)
        else:
            self.item(row, 3).setText("")

        # if isChecked:
        #     self.switchButton.setText(self.tr('On'))
        # else:
        #     self.switchButton.setText(self.tr('Off'))

    ### 新增方法：删除选中的行
    def delete_selected_rows(self):
        """删除用户选中的行"""
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())

        # 倒序删除避免索引错乱
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)

    ### 新增方法：清空所有行
    def clear_all_rows(self):
        """清空表格中的所有行"""
        self.setRowCount(0)
