import json
import requests
import pandas as pd
import numpy as np
import joblib
import boto3
from io import BytesIO
from datetime import datetime, timezone
import unicodedata

# Nome do bucket no S3
BUCKET_NAME = 'dados-clima'

# Inicializa o cliente S3
s3 = boto3.client('s3')

# Função para carregar arquivos serializados do S3
def load_from_s3(key):
    response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return joblib.load(BytesIO(response['Body'].read()))

# Carrega o modelo e o scaler
model = load_from_s3('modelos/svr_model.pkl')
scaler = load_from_s3('modelos/scaler.pkl')

def normalize_filename(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode().lower().replace(' ', '_')

def lambda_handler(event, context):
    cidades = {
        "Campinas": {"lat": -22.9056, "lon": -47.0608},
        "São Paulo": {"lat": -23.5505, "lon": -46.6333},
        "Rio de Janeiro": {"lat": -22.9068, "lon": -43.1729}
    }

    resultados_gerais = []

    for cidade, coords in cidades.items():
        # Monta a URL de previsão horária para a cidade
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}&"
            "hourly=temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,rain,weather_code,cloud_cover,wind_direction_10m,"
            "wind_speed_10m,is_day&timezone=America%2FSao_Paulo"
        )

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erro ao acessar API para {cidade}")
            continue

        data = response.json()
        df = pd.DataFrame(data['hourly'])
        df['time'] = pd.to_datetime(df['time'])

        now = pd.Timestamp.now().floor('h')
        future_df = df[df['time'] > now].copy()

        future_df['hour'] = future_df['time'].dt.hour
        future_df['month'] = future_df['time'].dt.month
        future_df['hour_sin'] = np.sin(2 * np.pi * future_df['hour'] / 24)
        future_df['hour_cos'] = np.cos(2 * np.pi * future_df['hour'] / 24)
        future_df['month_sin'] = np.sin(2 * np.pi * future_df['month'] / 12)
        future_df['month_cos'] = np.cos(2 * np.pi * future_df['month'] / 12)

        x_input = future_df.drop(columns=['temperature_2m', 'time', 'hour', 'month'], errors='ignore')
        x_scaled = scaler.transform(x_input)
        predictions = model.predict(x_scaled)

        result = [
            {
                "hora": t.isoformat(),
                #"cidade_": cidade,
                "previsao_temperatura": round(p, 2)
            }
            for t, p in zip(future_df['time'], predictions)
        ]

        resultados_gerais.extend(result)

        # Salva um arquivo por cidade no S3
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        data_particao = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        cidade_normalizada = normalize_filename(cidade)

        key = (
            f"previsoes/data={data_particao}/cidade={cidade_normalizada}/"
            f"{cidade_normalizada}_{timestamp}.json"
        )

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body='\n'.join(json.dumps(r) for r in result),
            ContentType='application/json'
        )

    return {
        "statusCode": 200,
        "body": json.dumps(resultados_gerais)
    }
