-- Modelo: fct_rides_completed
-- Camada: Gold
-- Descrição: Corridas concluídas — evento de receita do RideStream
-- Cada linha representa uma corrida finalizada com sucesso
-- Fonte: Silver layer (arquivos Parquet em data/silver/ride_events/)

{{
    config(
        materialized='table',
        tags=['gold', 'fato', 'receita']
    )
}}

-- Lê os Parquet da Silva diretamente via DuckDB (sem servidor)
-- O glob '**/*.parquet' captura todos os arquivos em qualquer partição year/month/day
with corridas_silver as (
    select *
    from read_parquet(
        'C:/Users/JosafaBarbosadosSant/ridestream-analytics-lakehouse/data/silver/ride_events/**/*.parquet',
        hive_partitioning = true
    )
),

-- Filtra apenas corridas concluídas — único status que gera receita
corridas_concluidas as (
    select
        ride_id,
        driver_id,
        passenger_id,
        timestamp as completed_at,
        fare as valor_corrida,
        rating as avaliacao,
        origin_lat,
        origin_lon,
        dest_lat,
        dest_lon,
        year,
        month,
        day
    from corridas_silver
    where status = 'completed'
      and ride_id is not null
      and driver_id is not null
      and fare is not null
)

select * from corridas_concluidas
