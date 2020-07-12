#!/usr/bin/env python
# coding: utf-8

# In[75]:


import requests  
import datetime
import json



"""
BotHandler - класс для получения и отправки сообщения через бота.

users_url_info - словарь в котором будут храниться данные о последних запросах пользователя.
    Ключ - id чата пользователя.

"""
class users_url_info():
    def __init__(self):
        self.url_dict = {} #словарь с данными 
    
    def make_new_entry(self,user_id): #user_id - id чата пользователя. Создает пустую запись для нового пользователя.
        self.url_dict[user_id] = {'last_ten_urls' :(None,)*10,  #кортеж, который хранит последние 10 ссылок
                                  'count_urls' :0 ,    #количество ссылоок в кортеже(если их меньше 10)
                                  'active_request' :False} #флаг: True - бот ждет ссылки, False - бот ждет выбор 1 или 2.
        
    def add_new_url(self,user_id , url_info): #добавление новой ссылки url_info для user_id пользователя
        self.url_dict[user_id]['last_ten_urls'] = (url_info,) + self.url_dict[user_id]['last_ten_urls'][:-1]
        if self.url_dict[user_id]['count_urls'] < 10:
            self.url_dict[user_id]['count_urls']+=1
        
        
        
class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        
        self.keyboard1 = {
                "keyboard":[[{"text": "1"}, {"text": "2"}]],
                "resize_keyboard":True
                }
        self.keyboard2 = {
                "keyboard":[[{"text": "3"}]],
                "resize_keyboard":True
                }
        
        self.keyboard1 = toJSON(self.keyboard1)
        self.keyboard2 = toJSON(self.keyboard2)

        
    def get_updates(self, offset=None, timeout=30): #получаем новые обновления 
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        
        try:
            resp = requests.get(self.api_url + method, params)
        except:
            print('Error getting updates')
            return None
        
        if not resp.status_code == 200: # проверяем пришедший статус ответа
            return None 
        
        if not resp.json()['ok']: 
            return None
        
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text, active_flag = False): #отправляем сообщение - text пользователю chat_id
                                                                #active_flag - True - если мы  
        if active_flag is False: 
            keyboard_main = self.keyboard1
        else:
            keyboard_main = self.keyboard2
            
        params = {'chat_id': chat_id, 'text': text,'reply_markup' : keyboard_main}
        method = 'sendMessage'
        
        try:
            resp = requests.post(self.api_url + method, params)
            print(resp)
        except:
            print('Send message error')
            return False
        
        return resp

    def get_last_update(self): #из новых обновлений берем последнее.
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[-1]
        else:
            last_update = None

        return last_update
    
    
    
def make_request_to_relink(users_url): #делаем запрос сервису для получения укороченной ссылки.
    r =  requests.post(url = "https://rel.ink/api/links/" , data = {"url" :users_url}).json()
    return r

def toJSON(object):
    return json.dumps(object, default=lambda o: o.__dict__,sort_keys=True, indent=4)


# In[76]:


def main(token):
    """
    Основная логика работы бота:
    
    Начало диалога: бот дает выбор: 1 - отправить ему ссылки 
                                    2 - показать историю ссылок 
    Выбор 1: принимает ссылки до тех пор пока не получит в ответ -"3".
    Выбор 2: отправляет последние запросы, если они есть.
    Иначе: не понимает, просит выбрать 1-2 еще раз.
    
    """
    bot = BotHandler(token)
    new_offset = None
    
    users_url = users_url_info() #словарь с ссылками 
    phrases = { 'hello' : "Привет, я - URLCutter.\n ",
                '2thing' : "Я умею делать 2 вещи:\n 1. Mогу обрезать твою ссылку.\n 2. Mогу показать твои последние 10 обрезанных ссылок.\n" , 
                'what_you_want' : "Скажи мне, что ты хочешь. Напиши: 1 или 2." ,
                'give_me_url' : "Хорошо. Отправь мне ссылку.",
                'dont_understand' : "Я тебя не понимаю.",
                'is_not_url' : "Это не ссылка. Попробуй еще раз.",
                'exit_from_1' : "Если больше не хочешь отправлять ссылки, напиши 3.",
                'no_have_10_urls' : "Ты мне еще ничего не отправлял."}
    
    
    while True:
        update = bot.get_updates(new_offset) #смотрим обновления только те, которые мы еще не смотрели.
        
        if update is None: #если их нет, то выходим 
            continue 
              
        for last_update in update: #проходим по непрочитанным сообщениям
            #last_update = bot.get_last_update()
            

            

            
            current_update_id = last_update['update_id']
            current_chat_id   = last_update['message']['chat']['id']
            current_chat_name = last_update['message']['chat']['first_name']
            
            if current_chat_id not in users_url.url_dict: #если пользователь новый 
                users_url.make_new_entry(current_chat_id) #добавляем запись в словарь с ссылками  
                
            active_flag = users_url.url_dict[current_chat_id]['active_request']
            
            
            if 'text' not in last_update['message']: # это просто текст или какая-нибудь картиночка?
                print('Unknown message')
                bot.send_message(current_chat_id, phrases['dont_understand'],active_flag)
                new_offset = current_update_id + 1
                continue
          
    
            
            current_chat_text = last_update['message']['text']
            
            

                
            
            
            
            if current_chat_text == "/start":#если новый пользователь 
                bot.send_message(current_chat_id, phrases['hello'])
                bot.send_message(current_chat_id, phrases['2thing'])
                bot.send_message(current_chat_id, phrases['what_you_want'])
                users_url.url_dict[current_chat_id]['active_request'] = False #если он вдруг не новый 
                
           # Случай когда мы выбрали  1 
            elif current_chat_text == "1" and active_flag is False: #если мы выбрали - 1 
                users_url.url_dict[current_chat_id]['active_request'] = True 
                bot.send_message(current_chat_id , phrases['give_me_url'] ,active_flag)
        
           # Случай когда бот ждет от нас ссылки для обработки.
                
            elif active_flag is True:
                
                #Если мы больше не хотим отправлять ссылки 
                if current_chat_text == "3":
                    users_url.url_dict[current_chat_id]['active_request'] = False
                    bot.send_message(current_chat_id ,phrases['what_you_want'])
                    
                else:
                
                    cutten_url_dict = make_request_to_relink(current_chat_text)
                    
                    if cutten_url_dict['url'] == current_chat_text: #если мы получили то что нужно
                        users_url.add_new_url(current_chat_id, cutten_url_dict)
                        bot.send_message(current_chat_id , cutten_url_dict['hashid'], active_flag)
                    else: #иначе говорим что это не ссылка.
                        bot.send_message(current_chat_id ,phrases['is_not_url'], active_flag)
                        bot.send_message(current_chat_id ,phrases['exit_from_1'], active_flag)
        
        
            # Случай когда бот показывает нам историю.
            
            elif current_chat_text == "2":
                count = users_url.url_dict[current_chat_id]['count_urls']
                reply_text = ""
                
                if count == 0: #если ссылок нет 
                    bot.send_message(current_chat_id ,phrases['no_have_10_urls'])
                else:
                    for i in range(count):
                        reply_text+=str(i + 1) + ". " + users_url.url_dict[current_chat_id]['last_ten_urls'][i]['hashid'] + " \n"
                    bot.send_message(current_chat_id ,reply_text)
            
            else: #иначе он не понимает что ему пишут.
                bot.send_message(current_chat_id, phrases['dont_understand'])
                bot.send_message(current_chat_id, phrases['2thing'])
                bot.send_message(current_chat_id, phrases['what_you_want'])
            
            
            new_offset = current_update_id + 1 #запоминаем обновление, чтобы смотреть только новые 
            
            
      
    


# In[73]:


token = "1263019262:AAGFzyAy2MaWooPIBB0ZgkKcUPxV8_0sVbM"


# In[77]:

if __name__ == '__main__':  
    try:
        main(token)
    except KeyboardInterrupt:
        exit()
