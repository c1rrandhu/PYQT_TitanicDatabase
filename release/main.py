# импортируем необходимые для работы библиотеки
import sys
import csv
import sqlite3
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QMessageBox, QFileDialog
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

# загружаем дизайны
from main_design import Ui_MainWindow
from editWindow_design import Edit_DB_Form
from photo_design import Ui_Form


# виджет главного окна
class TitanicDatabase(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('TitanicDatabase')

        # контролер для кнопки выгрузки
        self.contr = False

        # диалог для оповещения пустого запроса
        self.empty_search = EmptySearchMsgBox(parent=self)

        # диалог для оповещения об ошибке
        self.error_msg = ErrorMsgBox(parent=self)

        # сделаем текст в статусбаре побольше
        # и установим шрифт Times New Roman
        self.statusBar().setFont(QFont('Times', 20))

        # кнопка для выполнения запроса
        self.search_in_database.clicked.connect(self.search_in_db)
        # кнопка для запроса по фото с открытием диалога
        self.search_by_photo.clicked.connect(self.find_by_photo_in_db)
        # кнопка для внесения изменений в базу с открытием диалога
        self.edit_database.clicked.connect(self.edit_the_db)
        # кнопка для выгрузки CSV-файла
        self.load_csv_file.clicked.connect(self.load_csv)

        # подключаем базу данных
        self.connection = sqlite3.connect('release/data/database')
        cur = self.connection.cursor()
        result = cur.execute('''SELECT * FROM main''')

        # сохраняем все содержимое БД
        self.data = [x for x in result]
        self.headers = ['id', 'Выжил', 'Класс', 'Имя', 'Пол', 'Возраст', 'Братья/сестры', 'Дети',
                        '№ Билета', 'Цена', 'Каюта', 'Порт назначения']

        # Виджет для изменения БД
        self.edit_widget = EditDBWidget()

        # Виджет для поиска по фото
        self.photo_search = SearchByPhoto()

    # функция поиска запроса в БД
    def search_in_db(self):
        '''
        В качестве примера работы с приложением в базе данных
        хранятся персональные данные пассажиров Титаника.
        Данные были мной сформированы, опираясь на популярный датасет TitanicSubmission,
        используемый для отработки алгоритмов машинного обучения

        self.person_id - id пассажира в БД     (целое число от 1 до 891 включительно)
        self.alive - выжил ли человек на Титанике     (True/False)
        self.class_type - качество класса, в котором ехал пассажир    (1, 2 или 3)
        self.name - имя     (строка)
        self.sex - пол   (male/female)
        self.age - возраст    (целое число)
        self.siblings - количество родных братьев или сестер у пассажира   (целое число)
        self.child - количество детей у пассажира    (целое число)
        self.ticket - кодовый номер билета      (строка)
        self.price - стоимость билета    (вещественное число)
        self.room - кодовый номер каюты, в которой ехал пассажир    (строка)
        self.destination - порт назначения пассажира    (S - Саутгемптон, C - Шербур, Q - Куинстаун)
        '''

        # выгружаем значения всех ячеек
        line_input = [self.person_id.text(), self.alive.text(), self.class_type.text(),
                      self.name.text(), self.sex.text(), self.age.text(), self.siblings.text(),
                      self.child.text(), self.ticket.text(), self.price.text(), self.room.text(),
                      self.destination.text()]
        keys = self.headers
        # строка, в которую мы будем собирать SQL-запрос
        search = ''

        # пробегаемся циклом, проверяя на имеющиеся значения в ячейках
        for x in range(len(line_input)):
            if line_input[x]:
                # логические запросы
                if 'and' in line_input[x].lower() or 'or' in line_input[x].lower() or 'not' in line_input[x].lower():
                    temp = line_input[x].split()
                    for elem in range(len(temp)):
                        if temp[elem].lower() in ('and', 'or'):
                            temp.insert(elem + 1, keys[x])
                    search += str(keys[x] + ' '.join(temp) + " AND ")

                # операции с числами
                elif line_input[x][0] in ['=', '>', '<', '!']:
                    search += str(keys[x] + str(line_input[x]) + " AND ")

                # операции по маске
                elif '%' in line_input[x] or '_' in line_input[x]:
                    search += str(keys[x] + " LIKE '" + str(line_input[x]) + "' AND ")

                # обычные запросы
                else:
                    search += str(keys[x] + " = " + "'" + str(line_input[x]) + "'" + " AND ")

        # проверка на изначальный пустой ввод
        try:
            # подключаем базу данных
            cur = self.connection.cursor()
            res = cur.execute(f'''SELECT * FROM main WHERE {search[:-4]}''')
            search = [x for x in res]

        except Exception:
            search = ''
            self.contr = False

        # проверяем на смысл запроса
        if search:
            # очищаем статус бар
            self.statusBar().clearMessage()

            # заполняем дисплей
            self.tableWidget.setRowCount(len(search))
            self.tableWidget.setColumnCount(12)
            self.tableWidget.setHorizontalHeaderLabels(self.headers)

            # забиваем ячейки
            for row in range(len(search)):
                for col in range(len(search[row])):
                    self.tableWidget.setItem(row, col, QTableWidgetItem(str(search[row][col])))
                    self.contr = True
        else:
            # если запрос пустой, выводим в статус
            # бар соответствующее сообщение
            # и очищаем экран
            self.statusBar().showMessage('По данному запросу ничего не найдено')
            self.contr = False
            self.tableWidget.clear()

    # функция отображения виджета
    # поиска по фото
    def find_by_photo_in_db(self):
        self.photo_search.show()

    # функция отображения виджета
    # изменения базы данных
    def edit_the_db(self):
        self.edit_widget.show()

    # функция загрузки CSV-файла
    def load_csv(self):
        # в случае непредвиденной ошибки перехватим
        # ее, не дав программе упасть
        # Вместо этого выведем соответствующее сообщение
        try:
            # проверка на пустоту запроса
            if not self.contr:
                self.empty_search.exec()
            else:
                # забираем путь, указанный пользователем
                location = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV(*.csv);;txt(*.txt)')[0]
                # если путь "не пустой"
                if location:
                    filename = f'{location.split("/")[-1]}'
                    # создаем файл и заполняем дисплей tableWidget
                    with open(filename, 'w', encoding='utf8') as result:
                        writer = csv.writer(result, delimiter=';', quotechar="'")
                        writer.writerow(self.headers)
                        for row in range(self.tableWidget.rowCount()):
                            data = list()
                            for col in range(self.tableWidget.columnCount()):
                                item = self.tableWidget.item(row, col)
                                if item:
                                    data.append(item.text())
                                else:
                                    data.append('')
                            writer.writerow(data)
                        result.close()

        except Exception:
            # зададим диалогу дизайн:
            # сообщение шрифтом Times New Roman в 25 пунктов черного цвета
            # фон диалога покрасим в красный цвет
            self.error_message.setStyleSheet('color: rgb(255, 255, 255);'
                                             'background-color: rgb(255, 0, 0);'
                                             '\nfont: 75 25pt "Times New Roman";')
            self.error_msg.exec()

    # функция обработки горячих клавиш, которые
    # делают выгрузку CSV-файла
    # при сочетании ALT + SHIFT + S
    def keyPressEvent(self, event):
        if int(event.modifiers()) == (Qt.AltModifier + Qt.ShiftModifier):
            if event.key() == Qt.Key_S:
                self.load_csv()


# класс, предназначенный для виджета замены данных в БД
class EditDBWidget(QWidget, Edit_DB_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.setFixedSize(950, 450)
        self.setWindowTitle('Edit the database')

        # подключаем базу данных
        self.connection = sqlite3.connect('release/data/database')
        self.cur = self.connection.cursor()

        # подключаем диалоги для предупреждения
        # диалог для вставки значения
        self.message = MsgBox(parent=self)

        # диалог для ошибки
        self.error_message = ErrorMsgBox(parent=self)
        # зададим ему дизайн:
        # сообщение шрифтом Times New Roman в 25 пунктов черного цвета
        # фон диалога покрасим в красный цвет
        self.error_message.setStyleSheet('color: rgb(255, 255, 255);'
                                         'background-color: rgb(255, 0, 0);'
                                         '\nfont: 75 25pt "Times New Roman";')

        # диалог для изменения значения
        self.notify_message = NotifyMsgBox(parent=self)

        # кнопка удаления значения из БД
        self.delete_btn.clicked.connect(self.delete_value)
        # кнопка обновления значения в БД
        self.update_btn.clicked.connect(self.update_value)
        # кнопка вставки значения в БД
        self.insert_btn.clicked.connect(self.insert_value)

    # функция удаления значения из БД
    def delete_value(self):
        identify = self.db_person_id.text()
        criterion = self.criterion.text()
        try:
            if criterion:
                ret = self.message.exec()
                crit_inp = tuple(criterion.split())
                id_inp = tuple(map(int, identify.split()))
                if identify:
                    if ret == QMessageBox.Yes:
                        if len(id_inp) == 1:
                            if len(crit_inp) == 1:
                                self.cur.execute(f'''UPDATE main 
                                SET {crit_inp[0]} = ""
                                WHERE id = {id_inp[0]}''')
                                self.connection.commit()
                                self.notify_message.exec()
                            else:
                                self.cur.execute(f'''UPDATE main 
                                SET {crit_inp} = {tuple('' for _ in range(len(crit_inp)))}
                                WHERE id = {id_inp[0]}''')
                                self.connection.commit()
                                self.notify_message.exec()
                        else:
                            if len(crit_inp) == 1:
                                self.cur.execute(f'''UPDATE main 
                                SET {crit_inp[0]} = ""
                                WHERE id IN {id_inp}''')
                                self.connection.commit()
                                self.notify_message.exec()
                            else:
                                self.cur.execute(f'''UPDATE main 
                                SET {crit_inp} = {tuple('' for _ in range(len(crit_inp)))}
                                WHERE id IN {id_inp}''')
                                self.connection.commit()
                                self.notify_message.exec()
                else:
                    self.error_message.exec()
            else:
                if identify:
                    ret = self.message.exec()
                    to_drop = tuple(map(int, identify.split()))
                    if ret == QMessageBox.Yes:
                        if len(to_drop) == 1:
                            self.cur.execute(f'''DELETE FROM main WHERE id = {to_drop[0]}''')
                            self.connection.commit()
                            self.notify_message.exec()
                        else:
                            self.cur.execute(f'''DELETE FROM main WHERE id IN {to_drop}''')
                            self.connection.commit()
                            self.notify_message.exec()
                else:
                    self.error_message.exec()

            a = identify.split()
            if len(a) == 1:
                self.cur.execute(f'''DELETE FROM photos WHERE personId = {a[0]}''')
            else:
                self.cur.execute(f'''DELETE FROM photos WHERE personId IN {tuple(map(int, a))}''')
            self.connection.commit()

        except Exception:
            self.error_message.exec()

    # функция обновления значения в БД
    def update_value(self):
        # заберем id заменяемого пассажира
        identify = self.db_person_id.text()
        # заберем его критерий (может быть не указан)
        criterion = self.criterion.text()
        # прочитаем текущие значения в соответствующих ячейках
        line_input = [self.alive.text(), self.class_type.text(), self.name.text(), self.sex.text(),
                      self.age.text(), self.siblings.text(), self.child.text(), self.ticket.text(),
                      self.price.text(), self.room.text(), self.destination.text()]

        try:
            if criterion:
                ret = self.message.exec()
                crit_inp = tuple(criterion.split())
                id_inp = tuple(map(int, identify.split()))
                if ret == QMessageBox.Yes:
                    if len(id_inp) == 1:
                        if len(crit_inp) == 1:
                            for x in range(len(line_input)):
                                if line_input[x]:
                                    self.cur.execute(f'''UPDATE main 
                                            SET {crit_inp[0]} = "{line_input[x]}"
                                            WHERE id = {id_inp[0]}''')
                                    break
                            self.connection.commit()
                            self.notify_message.exec()
                        else:
                            to_search = []
                            for x in range(len(line_input)):
                                if line_input[x]:
                                    to_search.append(line_input[x])
                            self.cur.execute(f'''UPDATE main 
                                    SET {crit_inp} = {tuple(to_search)}
                                    WHERE id = {id_inp[0]}''')
                            self.connection.commit()
                            self.notify_message.exec()
                    else:
                        if len(crit_inp) == 1:
                            for x in range(len(line_input)):
                                if line_input[x]:
                                    self.cur.execute(f'''UPDATE main 
                                            SET {crit_inp[0]} = "{line_input[x]}"
                                            WHERE id IN {id_inp}''')
                                    break
                            self.connection.commit()
                            self.notify_message.exec()
                        else:
                            to_search = []
                            for x in range(len(line_input)):
                                if line_input[x]:
                                    to_search.append(line_input[x])
                            self.cur.execute(f'''UPDATE main 
                                    SET {crit_inp} = {tuple(to_search)}
                                    WHERE id IN {id_inp}''')
                            self.connection.commit()
                            self.notify_message.exec()
            else:
                ret = self.message.exec()
                to_change = tuple(map(int, identify.split()))
                if ret == QMessageBox.Yes:
                    if len(to_change) == 1:
                        self.cur.execute(f'''UPDATE main 
                        SET ('Выжил', 'Класс', 'Имя', 'Пол', 'Возраст', 'Братья/сестры', 'Дети',
                        'Билет', 'Цена', 'Каюта', 'Порт назначения') = {tuple(line_input)}
                        WHERE id = {to_change[0]}''')
                        self.connection.commit()
                        self.notify_message.exec()
                    else:
                        self.cur.execute(f'''UPDATE main 
                        SET ('Выжил', 'Класс', 'Имя', 'Пол', 'Возраст', 'Братья/сестры', 'Дети',
                        'Билет', 'Цена', 'Каюта', 'Порт назначения') = {tuple(line_input)}
                        WHERE id IN {to_change}''')
                        self.connection.commit()
                        self.notify_message.exec()

        except Exception:
            self.error_message.exec()

    # функция вставки нового значения в базу
    def insert_value(self):
        line_input = [self.alive.text(), self.class_type.text(), self.name.text(), self.sex.text(),
                      self.age.text(), self.siblings.text(), self.child.text(), self.ticket.text(),
                      self.price.text(), self.room.text(), self.destination.text()]
        id_cell = self.db_person_id.text()

        try:
            ret = self.message.exec()
            if ret == QMessageBox.Yes:
                to_insert = line_input.copy()
                if id_cell:
                    if len(id_cell.split()) == 1:
                        to_insert.insert(0, int(id_cell))
                        self.cur.execute(f'''INSERT INTO main VALUES {tuple(to_insert)}''')
                    else:
                        for x in id_cell.split():
                            total_insert = line_input.copy()
                            total_insert.insert(0, int(x))
                            self.cur.execute(f'''INSERT INTO main VALUES {tuple(total_insert)}''')
                            self.connection.commit()
                else:
                    self.cur.execute(f'''INSERT INTO main ('Выжил', 'Класс', 'Имя', 'Пол', 'Возраст', 
                    'Братья/сестры', 'Дети', 'Билет', 'Цена', 'Каюта', 'Порт назначения') 
                    VALUES {tuple(line_input)}''')
                self.connection.commit()
                self.notify_message.exec()

        except Exception:
            self.error_message.exec()


# класс, предназначенный для поиску по фото
class SearchByPhoto(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(720, 370)
        self.error_message = ErrorMsgBox(parent=self)
        self.error_message.setStyleSheet('background-color: rgb(0, 0, 0);\n'
                                         'font: 75 25pt "Times New Roman";')
        self.setWindowTitle('Search by photo')

        # подключаем базу данных
        self.db = sqlite3.connect('release/data/database')
        self.cur = self.db.cursor()

        # кнопка для произведения
        # поиска в БД по фотографии
        self.searchButton.clicked.connect(self.search)

    # функция поиска фото
    def search(self):
        person = self.personId.text()
        pixmap = ''
        try:
            if person:
                res = self.cur.execute(f'''SELECT photo FROM photos WHERE personId = {person}''')
                for x in res:
                    # размер лейбла, в который мы помещаем картинку, ограничен (350х290),
                    # поэтому, сохранив пиксмап, подгоним его под размер лейбла
                    pixmap = QPixmap(f'release/photos/{x[0]}').scaled(350, 290)
                self.photo_label.setPixmap(pixmap)
            else:
                # в случае изначально пустого ввода
                # оповестим пользователя об этом
                self.error_message.setText('Пустой ввод!')
                self.error_message.exec()
        except Exception:
            # в случае непредвиденной ошибки
            # сообщим об этом
            self.error_message.setText('Фотография не найдена')
            self.error_message.exec()


# класс диалога с выбором ответа (Да/Нет)
class MsgBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setText('Вы уверены?')
        self.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.setDefaultButton(QMessageBox.Yes)


# класс диалога с оповещением об ошибке
class ErrorMsgBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setText('Возникла ошибка!')
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


# класс диалога с оповещением об успешном выполнении запроса
class NotifyMsgBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setText('Запрос выполнен!')
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


# класс диалога об оповещении пустого запроса
class EmptySearchMsgBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setText('Файл пуст!')
        self.setStandardButtons(QMessageBox.Ok)
        self.setDefaultButton(QMessageBox.Ok)


# запуск кода
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TitanicDatabase()
    ex.show()
    sys.exit(app.exec())
