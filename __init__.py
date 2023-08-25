##Implementando la logica de la APP aqui
#Cuando se reciben valores fuera de rango se envian comandos para
#realizar una acción

from typing import List
import logging

import azure.functions as func

import json
import os
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod

potencia_trafo = 100000

umbral_vac_min = 198
umbral_vac_max = 242

#umbrales corriente
umbral_amp_max = 0.8 * potencia_trafo / (220 * 1.732)

#umbral de temperatura maxima
umbral_temp_max = 35
temp_correccion = 30

def main(event: func.EventHubEvent):
    body = json.loads(event.get_body().decode('utf-8'))
    device_id = event.iothub_metadata['connection-device-id']

    logging.info(f'Received message: {body} from {device_id}')

    vfr = body['voltajeData']['FR']
    vfs = body['voltajeData']['FS']
    vft = body['voltajeData']['FT']
    cfr = body['corrienteData']['FR']
    cfs = body['corrienteData']['FS']
    cft = body['corrienteData']['FT']
    temp = body['temperaturaData']

    #Implementar formula de umbral de corriente en base de temperatura.

    # 
    # Potencia por fase: Multiplicar Cada fase entre su voltaje * corriente
    # Formula correccion potencia nominal norma IEEE:C57.92 (110- temp / 80)
    # Luego aplicar el 80% para la alerta a la nueva potencia nominal

    logging.info(f'Temperatura: {temp} Volts {vfr} Corriente: {cfr}')

    if (( vfr > umbral_vac_max) or (vfr < umbral_vac_min )):
        vac_on = True
    else:
        vac_on = False

    if ( temp > umbral_temp_max):
        temp_on = True
    else:
        temp_on = False
    #Preguntar si se necesita corregir la corriente maxima
    if (temp > temp_correccion):
       umbral_amp_max = 0.8 * potencia_trafo * (110 - temp) / (220 * 1.732 * 80)
    else:   
       umbral_amp_max = 0.8 * potencia_trafo / (220 * 1.732)

    if ( cfr > umbral_amp_max):
        amp_on = True
    else:
        amp_on = False
    

    direct_method = CloudToDeviceMethod(method_name='anomalia_detectada', payload=  {"vac_on": vac_on, "amp_on": amp_on , "temp_on": temp_on})
        

    registry_manager_connection_string = os.environ['REGISTRY_MANAGER_CONNECTION_STRING']
    registry_manager = IoTHubRegistryManager(registry_manager_connection_string)    
    registry_manager.invoke_device_method(device_id, direct_method)
