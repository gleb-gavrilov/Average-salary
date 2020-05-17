import requests
from terminaltables import SingleTable
import argparse


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']:
        if vacancy['salary']['currency'] == 'RUR':
            return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])
    return None


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        return predict_salary(vacancy['payment_from'], vacancy['payment_to'])
    return None


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    return None


def get_vacancies_from_superjob(search_vacancy_name, page, token_sj):
    headers = {
        'X-Api-App-Id': token_sj
    }
    params = {
        'town': 4,
        'keyword': search_vacancy_name,
        'count': 100,
        'page': page
    }
    response = requests.get('https://api.superjob.ru/2.0/vacancies/', params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_vacancies_from_hh(vacancy, page, headers):
    params = {
        'text': vacancy,
        'area': 1,
        'per_page': 100,
        'period': 30,
        'page': page,
        'only_with_salary': True
    }
    response = requests.get('https://api.hh.ru/vacancies', params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def get_data_from_hh(search_vacancies_names, headers):
    vacancies_info = []
    for search_vacancy_name in search_vacancies_names:
        all_salary = 0
        vacancies_count = 0
        total = 0
        for page in range(0, 999):
            vacancies = get_vacancies_from_hh(search_vacancy_name, page, headers)
            for vacancy in vacancies['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    all_salary += salary
                    vacancies_count += 1
            if page >= vacancies['pages'] - 1:
                total = vacancies['found']
                break
        vacancies_info.append({
            'vacancies_found': total,
            'vacancy': search_vacancy_name,
            'vacancies_processed': vacancies_count,
            'average_salary': int(all_salary / vacancies_count)
        })

    return vacancies_info


def get_data_from_superjob(search_vacancies_names, token_sj):
    vacancies_info = []
    for search_vacancy_name in search_vacancies_names:
        all_salary = 0
        vacancies_count = 0
        total = 0
        for page in range(0, 999):
            vacancies = get_vacancies_from_superjob(search_vacancy_name, page, token_sj)
            for vacancy in vacancies['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    all_salary += salary
                    vacancies_count += 1
            if not vacancies['more']:
                total = vacancies['total']
                break
        vacancies_info.append({
            'vacancies_found': total,
            'vacancy': search_vacancy_name,
            'vacancies_processed': vacancies_count,
            'average_salary': int(all_salary / vacancies_count)
        })
    return vacancies_info


def print_table(datasets, title):
    headers = ['Вакансия', 'Найдено вакансий', 'Обработано вакансий', 'Средняя зарплата']
    vacancies_name = [dataset['vacancy'] for dataset in datasets]
    vacancies_found = [dataset['vacancies_found'] for dataset in datasets]
    vacancies_processed = [dataset['vacancies_processed'] for dataset in datasets]
    vacancies_average_salary = [dataset['average_salary'] for dataset in datasets]
    table_data = [
        headers,
        [vacancies_name[0], vacancies_found[0], vacancies_processed[0], vacancies_average_salary[0]],
        [vacancies_name[1], vacancies_found[1], vacancies_processed[1], vacancies_average_salary[1]],
        [vacancies_name[2], vacancies_found[2], vacancies_processed[2], vacancies_average_salary[2]]
    ]

    table_instance = SingleTable(table_data, title)
    table_instance.justify_columns[2] = 'right'
    print(table_instance.table)
    print()


def main():
    parser = argparse.ArgumentParser(description='Расчёт средней зарплаты')
    parser.add_argument('-sj', type=str, default=None, help='Secret key от SuperJob')
    args = parser.parse_args()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
    }
    search_vacancies_names = ['Программист Python', 'Программист Java', 'Программист PHP']
    try:
        hh_info = get_data_from_hh(search_vacancies_names, headers)
        print_table(hh_info, 'HeadHunter')
        if args.sj:
            sj_info = get_data_from_superjob(search_vacancies_names, args.sj)
            print_table(sj_info, 'SuperJob')
    except requests.HTTPError as error:
        print(f'Can`t get data:\n{error}')
    except KeyError as error:
        print(error)


if __name__ == '__main__':
    main()
