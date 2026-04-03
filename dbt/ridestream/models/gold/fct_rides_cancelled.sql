-- Modelo: fct_rides_cancelled
-- Camada: Gold
-- Descrição: Corridas canceladas — evento de perda de receita do RideStream
-- Cada linha representa uma corrida que não foi concluída
-- Fonte: Silver layer (arquivos Parquet em data/silver/ride_events/)

{{
    config(
        materialized='table',
        tags=['gold', 'fato', 'cancelamento']
    )
}}

with corridas_silver as (
    select *
    from read_parquet(
        'C:/Users/JosafaBarbosadosSant/ridestream-analytics-lakehouse/data/silver/ride_events/**/*.parquet',
        hive_partitioning = true
    )
),

corridas_canceladas as (
    select
        ride_id,
        driver_id,
        passenger_id,
        timestamp as cancelled_at,
        origin_lat,
        origin_lon,
        year,
        month,
        day
    from corridas_silver
    where status = 'cancelled'
      and ride_id is not null
)

select * from corridas_canceladas
