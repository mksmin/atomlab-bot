import pandas as pd
import re
import datetime
import os


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


# async def get_program_schedule(tg_title):
#     """
#     function accept telegram chat's id,
#     connect to DB and accept name of file,
#     return to user time of study program
#
#     WARNING: устаревшая версия кода, нужно связать с ID чатом,
#     и подгружать расписание исходя из этого
#     файлы можно назвать с ключом chat_id
#
#     Возможно хранить расписание в БД
#
#     :param tg_title: int is id of telegram chat
#     :return: ...
#     """
#
#     match = re.search(r' \(', tg_title)
#
#     if match:
#         pattern = tg_title.find(' (')
#         if pattern:
#             name_xls = tg_title[:pattern]
#     else:
#         name_xls = 'notxls'
#         print('Возникла ошибка')
#
#     path = os.path.normpath(
#         os.path.join(os.path.dirname(__file__),
#                      f'..\\media\\Расписание\\{name_xls}.xlsx'))
#     result = os.path.isfile(path)
#
#     match result:
#         case True:
#             with pd.ExcelFile(path) as xls:
#                 df1 = pd.read_excel(xls, 0, index_col=None, na_values=["NA"])
#             date = datetime.date.today()
#             sheet_ind = df1.keys()
#             # Дописать эту часть кода, чтобы выводил другой результат, если дата не совпадает
#             for i in sheet_ind:
#                 str_i = str(i)
#                 date = str(date)
#                 if date in str_i:
#                     print(f'Эта дата есть в таблице')
#                     index_row = i
#                     break
#             index = 0
#             count_ = df1[index_row].count()
#             data_message = []
#             while index <= count_:
#                 start_time = df1['Start'].loc[index]
#                 end_time = df1['End'].loc[index]
#
#                 if str(df1[index_row].loc[index]) != 'nan':
#                     data = (
#                         f'\n\n{str(start_time)[:str(start_time).rfind(':')]}—{str(end_time)[:str(end_time).rfind(':')]}'
#                         f'\n{df1[index_row].loc[index]}')
#                     data_message.append(data)
#                     index += 1
#                 else:
#                     print('Значение равно False')
#                     index += 1
#                     continue
#
#             time_list = ' '.join(data_message)
#             return time_list
#         case _:
#             time_list = 'Возникла ошибка'
#             return time_list
