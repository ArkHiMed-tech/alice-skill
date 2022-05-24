'''Script for Alice's skill'''

import pymorphy2
from food import food
import random
from num2words import num2words

units = {
    'килограмм': 1000,
    'грамм': 1,
    'милиграмм': 0.001,
    'тонна': 1000000
}

analyser = pymorphy2.MorphAnalyzer(lang='ru')


def parse(inp: str):
    nums = []
    fin = []
    for i, word in enumerate(inp.split()):
        if word.isnumeric():
            nums.append(i)
    
    for i in nums:
        if analyser.parse(inp.split()[i + 1])[0].normal_form in units:
            ap = {'name': analyser.parse(inp.split()[i + 2])[0].normal_form, 'units': analyser.parse(inp.split()[i + 1])[0].normal_form, 'weight': int(inp.split()[i]), 'countable': False}
            fin.append(ap)
        elif analyser.parse(inp.split()[i + 1])[0].normal_form in food:
            ap = {'name': analyser.parse(inp.split()[i + 1])[0].normal_form, 'pieces': int(inp.split()[i]), 'countable': True}
            fin.append(ap)
        elif analyser.parse(inp.split()[i + 1])[0].normal_form not in food:
            fin.insert(0, 'No food')
        else:
            fin.insert(0, 'Error')
    
    return fin


sessionStorage = {}

def main(event, context):
    '''The main block of code'''

    inp = event

    response = {}

    response['session'] = inp['session']
    response['version'] = inp['version']
    response['response'] = {'end_session': False}

    if inp['session']['new']:
        response['response']['text'] = 'Привет! Сейчас я помогу тебе рассчитать калорийность пищи. Скажи мне например: "Сколько калорий в ста граммах риса?"'
        if sessionStorage.get(inp['session']['application']['application_id']) is None:
            sessionStorage[inp['session']['application']['application_id']] = {}
        sessionStorage[inp['session']['application']['application_id']]['state'] = 'main_menu'
    elif any([i in inp['request']['command'] for i in ['помощь', 'что ты умеешь']]):
        response['response']['text'] = 'Это навык Ccalc, я могу посчитать калории в пище и составить рацион питания на день. Для того, чтобы узнать, сколько калорий в том или ином продукте, просто скажите: "Сколько калорий в ста граммах муки?" или же: "Сколько калорий в пяти бананах?".'
        response['response']['tts'] = 'Это навык си калк , я могу посчитать калории в пище . Для того , чтобы узнать , сколько калорий в том или ином продукте , просто скажите сколько калорий в ста граммах муки ? или же , сколько калорий в пяти бананах ?'
    else:
        text = [analyser.parse(i)[0].normal_form for i in inp['request']['command'].split()]
        tags = parse(inp['request']['command'])
        if len(tags) == 0 or tags[0] == 'Error':
            response['response']['text'] = 'Извините, не поняла вас. Попробуйте переформулировать предложение'
        elif tags[0] == 'No food':
            response['response']['text'] = 'К сожалению, я еще не знаю, сколько в этом продукте калорий'
        else:
            tag = tags[0]
            product = food.get(tag['name'])
            if product is not None:
                name = tag['name']
                if tag['countable'] and product['countable']:
                    pieces = tag['pieces']
                    name = analyser.parse(tag['name'])[0].make_agree_with_number(pieces).inflect({'loct'} if pieces == 1 else {'plur', 'loct'}).word
                    calories = round((product['per_one'] * pieces) * (product['calories'] / 100), 3)
                    variants_text = [
                        f'В {pieces} {name} {calories} килокалорий',
                        f'Здесь содержится {calories} килокалорий',
                        f'Тут {calories} килокалорий',
                        f'В этом продукте {calories} килокалорий'
                    ]
                    calories = num2words(round((product['per_one'] * pieces) * (product['calories'] / 100), 3), lang='ru')
                    pieces = ' '.join([analyser.parse(i)[0].inflect({'gent'}).word for i in num2words(pieces, lang='ru').split()])
                    variants_tts = [
                        f'В {pieces} {name} {calories} килокалорий',
                        f'Здесь содержится {calories} килокалорий',
                        f'Тут {calories} килокалорий',
                        f'В этом продукте {calories} килокалорий'
                    ]
                    variant = random.choice([0, 1, 2, 3])
                    response['response']['tts'] = variants_tts[variant]
                    response['response']['text'] = variants_text[variant] 
                elif not tag['countable']:
                    unit = tag['units']
                    weight_u = tag['weight'] * units[unit]
                    name = analyser.parse(tag['name'])[0].inflect({'gent'}).word
                    calories = round(product['calories'] * (weight_u / 100), 3)
                    variants_text = [
                        f'Здесь содержится {calories} калорий',
                        f'Тут {calories} калорий',
                        f'В этом продукте {calories} калорий',
                        f'В {weight_u} {analyser.parse("грамм")[0].make_agree_with_number(weight_u).inflect({"loct"}).word} {name} {calories} калорий'
                    ]
                    calories = num2words(round(product['calories'] * (weight_u / 100), 3), lang='ru')
                    weight = ' '.join([analyser.parse(i)[0].inflect({'loct'}).word for i in num2words(weight_u, lang='ru').split()])
                    variants_tts = [
                        f'Здесь содержится {calories} калорий',
                        f'Тут {calories} калорий',
                        f'В этом продукте {calories} калорий',
                        f'В {weight} {analyser.parse("грамм")[0].make_agree_with_number(weight_u).inflect({"loct"}).word} {name} {calories} калорий'
                    ]
                    variant = random.choice([0, 1, 2, 3])
                    response['response']['tts'] = variants_tts[variant]
                    response['response']['text'] = variants_text[variant] 
                else:
                    variants = ['Что-то не расслышала. Повторите, пожалуйста.',
                                'Кажется, я вас не поняла. Можете сказать еще раз?',
                                'Прошу прощения, но я вас не поняла, повторите, пожалуйста, еще разок.']
                    response['response']['text'] = random.choice(variants)
            else:
                response['response']['text'] = 'К сожалению, я еще не знаю, сколько в этом продукте калорий'

    #else:
    #    response['response']['text'] = str(sessionStorage)

    return response
