import json
import requests
import datetime

class Mindicador:
 
    def __init__(self, indicador, year):
        self.indicador = indicador
        self.year = year
     
    def InfoApi(self):
        # En este caso hacemos la solicitud para el caso de consulta de un indicador en un año determinado
        url = f'https://mindicador.cl/api/{self.indicador}/{self.year}'
        response = requests.get(url)
        data = json.loads(response.text.encode("utf-8"))
        return data

def pago(fecha,
         row,
         deuda_uf, 
         deuda_dol_sin_interes, 
         deuda_dol_con_interes, 
         pago_uf, 
         pago_usd_sin_interes, 
         pago_usd_con_interes):
    
    interes_anual = 0.04
    interes_anual_dolares = 0.0412
    Deudauf = float(deuda_uf)
    Deudadol_sin_interes = float(deuda_dol_sin_interes)
    Deudadol_con_interes = float(deuda_dol_con_interes)
    if isinstance(fecha, str):
        penultimo_pago = datetime.datetime.strptime(fecha, "%d-%m-%Y").date()
    else:
        penultimo_pago = fecha.date()  # already datetime
    ultimo_pago = datetime.date.today()
    ultimo_pago_formato = datetime.date.today().strftime('%d-%m-%Y')
    
    dif_en_dias = ultimo_pago-penultimo_pago
    
    dif_en_dias = dif_en_dias.days
    
    cuota_en_pesos = float(pago_uf)
    cuota_en_dolares_sin = float(pago_usd_sin_interes)
    cuota_en_dolares_con = float(pago_usd_con_interes)
    
    ##calculo de uf
    Cla = Mindicador('uf',datetime.date.today().strftime('%d-%m-%Y'))
    Uf = Cla.InfoApi()['serie'][0]['valor']
    ###
    
    #calculo intereses
    interes_uf = (Deudauf*interes_anual)*(dif_en_dias/365)
    interes_dolar = (Deudadol_con_interes*interes_anual_dolares)*(dif_en_dias/365)
    
    nueva_deuda_uf = round(Deudauf+interes_uf-(cuota_en_pesos/Uf),3)
    nueva_deuda_usd_sin_interes = round(Deudadol_sin_interes-cuota_en_dolares_sin,3)
    nueva_deuda_usd_con_interesround = round(Deudadol_con_interes+interes_dolar-cuota_en_dolares_con,3)
    
    string_to_print = [f'{deuda_uf} UF + {deuda_dol_sin_interes} USD Total + {deuda_dol_con_interes} USD% Total con 4.12 % de interés anual {fecha} \n',
                        f'- {round(pago_uf/Uf,3)} UF (${pago_uf} con uf en {Uf} al {ultimo_pago_formato}) \n',
                        f'- Deuda de {round(pago_usd_sin_interes,3)} USD sin interes \n',
                        f'- Deuda de  {round(pago_usd_con_interes,3)} USD con interes \n',
                        f'+ {round(interes_uf,3)} UF por intereses de {dif_en_dias} días \n',
                        f'+ {round(interes_dolar,3)} USD por intereses de {dif_en_dias} días \n',
                        f'= {nueva_deuda_uf} UF + {nueva_deuda_usd_sin_interes} USD Total + {nueva_deuda_usd_con_interesround} USD% Total con 4.12 % de interés anual {ultimo_pago_formato}']
    
    return ultimo_pago_formato, nueva_deuda_uf, nueva_deuda_usd_sin_interes, nueva_deuda_usd_con_interesround, string_to_print