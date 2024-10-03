import logging
import sys
import pandas as pd
import os
logger = logging.getLogger("pool_loger")
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler("pool_logs.log", encoding='utf-8')
logger.addHandler(ch)


def read_activity_file(file_path):
    try:
        activity_df = pd.read_csv(file_path, sep='\t')
        return activity_df
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден.")
        print(f"Файл {file_path} не найден.")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Файл {file_path} пуст.")
        print(f"Файл {file_path} пуст.")
        return None
    except pd.errors.ParserError as e:
        logger.error(f"Ошибка парсинга файла {file_path}: {e}")
        print(f"Ошибка парсинга файла {file_path}: {e}")
        return None


def calculate_time_in_pools(activity_df):
    # Преобразование колонки 'Date' в datetime
    activity_df['Date'] = pd.to_datetime(activity_df['Date'])
    # Сортировка данных по атлетам, бассейнам и времени
    activity_df = activity_df.sort_values(['Athlete ID', 'Location', 'Date'])
    # Группировка данных по атлетам и бассейнам
    grouped_df = activity_df.groupby(['Athlete ID', 'Location'])
    # Рассчитываем время, проведённое в каждом бассейне
    time_in_pools = []
    for name, group in grouped_df:
        in_time = group[group['Type'] == 'In']['Date'].min()
        out_time = group[group['Type'] == 'Out']['Date'].max()
        if pd.isnull(in_time) or pd.isnull(out_time):
            # Вывод в лог, если данных о входе или выходе нет
            logger.error(f"Недостаточно данных для атлета {name[0]} в бассейне {name[1]}")
            print(f"Недостаточно данных для атлета {name[0]} в бассейне {name[1]}")
        else:
            time_in_pools.append({'Athlete ID': name[0], 'Location': name[1], 'Time': out_time - in_time})
    return pd.DataFrame(time_in_pools)


def calculate_time_in_complex(activity_df):
    # Группировка данных по атлетам
    grouped_df = activity_df.groupby('Athlete ID')
    # Рассчитываем время, проведённое в комплексе
    time_in_complex = []
    for name, group in grouped_df:
        in_time = group[group['Type'] == 'In']['Date'].min()
        out_time = group[group['Type'] == 'Out']['Date'].max()
        if pd.isnull(in_time) or pd.isnull(out_time):
            # Вывод в лог, если данных о входе или выходе нет
            logger.error(f"Недостаточно данных для атлета {name}")
            print(f"Недостаточно данных для атлета {name}")
        else:
            time_in_complex.append({'Athlete ID': name, 'Time': out_time - in_time})

    return pd.DataFrame(time_in_complex)


def save_results(time_in_pools, time_in_complex):
    time_in_pools.to_csv('time_in_pools.csv', index=False)
    time_in_complex.to_csv('time_in_complex.csv', index=False)


def main():
    file_path = 'activity.csv'
    activity_df = read_activity_file(file_path)
    if activity_df is not None:
        time_in_pools = calculate_time_in_pools(activity_df)
        time_in_complex = calculate_time_in_complex(activity_df)
        save_results(time_in_pools, time_in_complex)


if __name__ == "__main__":
    main()