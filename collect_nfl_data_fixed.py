#!/usr/bin/env python3
"""
Script corrigido para coletar dados históricos da NFL (2010-2024)
"""

import nfl_data_py as nfl
import pandas as pd
import numpy as np
from datetime import datetime
import os

def clean_data_types(df):
    """Limpa tipos de dados problemáticos"""
    
    # Converter colunas problemáticas para string
    string_cols = ['jersey_number', 'status']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    # Converter datas
    date_cols = ['birth_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df

def collect_historical_data():
    """Coleta dados históricos da NFL de 2010 a 2024"""
    
    print("🏈 Coletando dados históricos da NFL (2010-2024)")
    print("=" * 60)
    
    # Definir anos para coleta
    years = list(range(2010, 2025))  # 2010 a 2024
    print(f"📅 Anos para coleta: {years}")
    
    # Criar diretório para dados
    data_dir = "/home/ubuntu/nfl_data"
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # 1. Coletar dados semanais (principal para fantasy)
        print(f"\n📈 1. Coletando dados semanais...")
        weekly_data = nfl.import_weekly_data(years=years)
        print(f"   ✅ Dados semanais: {weekly_data.shape}")
        
        # Filtrar apenas posições de fantasy
        fantasy_positions = ['QB', 'RB', 'WR', 'TE']
        weekly_fantasy = weekly_data[weekly_data['position'].isin(fantasy_positions)].copy()
        print(f"   🎯 Dados de fantasy: {weekly_fantasy.shape}")
        
        # Salvar dados semanais como CSV (mais compatível)
        weekly_fantasy.to_csv(f"{data_dir}/weekly_fantasy_data.csv", index=False)
        print(f"   💾 Salvos em: weekly_fantasy_data.csv")
        
        # 2. Coletar dados de temporada
        print(f"\n📊 2. Coletando dados de temporada...")
        seasonal_data = nfl.import_seasonal_data(years=years, s_type='REG')
        print(f"   ✅ Dados de temporada: {seasonal_data.shape}")
        
        # Salvar dados de temporada
        seasonal_data.to_csv(f"{data_dir}/seasonal_data.csv", index=False)
        print(f"   💾 Salvos em: seasonal_data.csv")
        
        # 3. Coletar informações de times
        print(f"\n🏟️ 3. Coletando informações de times...")
        team_data = nfl.import_team_desc()
        print(f"   ✅ Dados de times: {team_data.shape}")
        
        # Salvar dados de times
        team_data.to_csv(f"{data_dir}/team_data.csv", index=False)
        print(f"   💾 Salvos em: team_data.csv")
        
        # 4. Coletar rosters históricos
        print(f"\n👥 4. Coletando rosters históricos...")
        roster_data = nfl.import_seasonal_rosters(years=years)
        print(f"   ✅ Dados de rosters: {roster_data.shape}")
        
        # Filtrar apenas posições de fantasy
        roster_fantasy = roster_data[roster_data['position'].isin(fantasy_positions)].copy()
        print(f"   🎯 Rosters de fantasy: {roster_fantasy.shape}")
        
        # Limpar tipos de dados
        roster_fantasy = clean_data_types(roster_fantasy)
        
        # Salvar dados de rosters
        roster_fantasy.to_csv(f"{data_dir}/roster_fantasy_data.csv", index=False)
        print(f"   💾 Salvos em: roster_fantasy_data.csv")
        
        # 5. Análise dos dados coletados
        print(f"\n🔍 5. Análise dos dados coletados...")
        
        print(f"\n📊 Estatísticas dos dados semanais:")
        print(f"   📅 Anos: {sorted(weekly_fantasy['season'].unique())}")
        print(f"   🏈 Times: {len(weekly_fantasy['recent_team'].unique())}")
        print(f"   👤 Jogadores únicos: {len(weekly_fantasy['player_id'].unique())}")
        
        # Contar jogadores por posição
        print(f"\n🎯 Jogadores por posição (dados semanais):")
        for pos in fantasy_positions:
            pos_count = len(weekly_fantasy[weekly_fantasy['position'] == pos]['player_id'].unique())
            print(f"   {pos}: {pos_count} jogadores únicos")
        
        # Verificar colunas importantes para fantasy
        fantasy_cols = [col for col in weekly_fantasy.columns if any(keyword in col.lower() for keyword in 
                       ['fantasy', 'points', 'yards', 'touchdown', 'td', 'reception', 'target', 'carry'])]
        
        print(f"\n🏆 Colunas de fantasy disponíveis ({len(fantasy_cols)}):")
        for col in sorted(fantasy_cols):
            print(f"   - {col}")
        
        # 6. Criar dataset consolidado para Streamlit
        print(f"\n🔧 6. Criando dataset consolidado...")
        
        # Adicionar informações de time aos dados semanais
        team_info = team_data[['team_abbr', 'team_name', 'team_logo_espn', 'team_color', 'team_color2']].copy()
        team_info.columns = ['team', 'team_name', 'team_logo', 'team_color', 'team_color2']
        
        # Merge com dados semanais
        weekly_consolidated = weekly_fantasy.merge(team_info, left_on='recent_team', right_on='team', how='left')
        
        # Adicionar informações básicas de roster (sem problemas de tipo)
        roster_info = roster_fantasy[['season', 'team', 'player_id', 'height', 'weight', 'college']].copy()
        weekly_consolidated = weekly_consolidated.merge(
            roster_info, 
            on=['season', 'player_id'], 
            how='left',
            suffixes=('', '_roster')
        )
        
        print(f"   ✅ Dataset consolidado: {weekly_consolidated.shape}")
        
        # Salvar dataset consolidado
        weekly_consolidated.to_csv(f"{data_dir}/consolidated_fantasy_data.csv", index=False)
        print(f"   💾 Salvos em: consolidated_fantasy_data.csv")
        
        # 7. Criar datasets por posição
        print(f"\n📂 7. Criando datasets por posição...")
        
        for pos in fantasy_positions:
            pos_data = weekly_consolidated[weekly_consolidated['position'] == pos].copy()
            pos_data.to_csv(f"{data_dir}/{pos.lower()}_data.csv", index=False)
            print(f"   💾 {pos}: {pos_data.shape} -> {pos.lower()}_data.csv")
        
        # 8. Criar resumo dos dados
        print(f"\n📋 8. Criando resumo dos dados...")
        
        summary = {
            'collection_date': datetime.now().isoformat(),
            'years_collected': years,
            'total_weekly_records': len(weekly_consolidated),
            'total_players': len(weekly_consolidated['player_id'].unique()),
            'positions': fantasy_positions,
            'teams': len(weekly_consolidated['recent_team'].unique()),
            'columns_available': len(weekly_consolidated.columns),
            'fantasy_columns': fantasy_cols,
            'files_created': [
                'weekly_fantasy_data.csv',
                'seasonal_data.csv', 
                'team_data.csv',
                'roster_fantasy_data.csv',
                'consolidated_fantasy_data.csv',
                'qb_data.csv',
                'rb_data.csv', 
                'wr_data.csv',
                'te_data.csv'
            ]
        }
        
        # Salvar resumo
        import json
        with open(f"{data_dir}/data_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"   💾 Resumo salvo em: data_summary.json")
        
        print(f"\n✅ Coleta de dados concluída com sucesso!")
        print(f"📁 Todos os arquivos salvos em: {data_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na coleta de dados: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """Cria dados de amostra para desenvolvimento rápido"""
    
    print(f"\n🔧 Criando dados de amostra para desenvolvimento...")
    
    data_dir = "/home/ubuntu/nfl_data"
    
    try:
        # Carregar dados consolidados
        df = pd.read_csv(f"{data_dir}/consolidated_fantasy_data.csv")
        
        # Criar amostra dos últimos 3 anos
        sample_years = [2022, 2023, 2024]
        sample_data = df[df['season'].isin(sample_years)].copy()
        
        print(f"   📊 Amostra criada: {sample_data.shape}")
        print(f"   📅 Anos: {sorted(sample_data['season'].unique())}")
        
        # Salvar amostra
        sample_data.to_csv(f"{data_dir}/sample_fantasy_data.csv", index=False)
        print(f"   💾 Amostra salva em: sample_fantasy_data.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar amostra: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando coleta de dados históricos da NFL")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Executar coleta
    success = collect_historical_data()
    
    if success:
        create_sample_data()
        print(f"\n🎉 Processo concluído com sucesso!")
    else:
        print(f"\n❌ Processo falhou!")
