#!/usr/bin/env python3
"""
Módulo de insights avançados para NFL Fantasy Analytics
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional

def calculate_rookie_insights(df: pd.DataFrame) -> Dict:
    """Calcula insights sobre performance de rookies por posição"""
    
    # Identificar rookies
    player_first_season = df.groupby('player_id')['season'].min().reset_index()
    player_first_season.columns = ['player_id', 'rookie_season']
    
    df_with_rookie = df.merge(player_first_season, on='player_id', how='left')
    df_with_rookie['is_rookie'] = df_with_rookie['season'] == df_with_rookie['rookie_season']
    
    insights = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_data = df_with_rookie[df_with_rookie['position'] == position]
        
        rookie_avg = pos_data[pos_data['is_rookie']]['fantasy_points_ppr'].mean()
        veteran_avg = pos_data[~pos_data['is_rookie']]['fantasy_points_ppr'].mean()
        
        # Calcular top rookies históricos
        top_rookies = pos_data[pos_data['is_rookie']].groupby(['player_display_name', 'rookie_season']).agg({
            'fantasy_points_ppr': 'sum'
        }).reset_index().nlargest(5, 'fantasy_points_ppr')
        
        # Padrões de adaptação (primeiras 4 semanas vs resto da temporada)
        rookie_early = pos_data[(pos_data['is_rookie']) & (pos_data['week'] <= 4)]['fantasy_points_ppr'].mean()
        rookie_late = pos_data[(pos_data['is_rookie']) & (pos_data['week'] > 4)]['fantasy_points_ppr'].mean()
        
        insights[position] = {
            'rookie_avg': rookie_avg,
            'veteran_avg': veteran_avg,
            'performance_gap': veteran_avg - rookie_avg,
            'gap_percentage': ((veteran_avg - rookie_avg) / veteran_avg * 100) if veteran_avg > 0 else 0,
            'top_rookies': top_rookies,
            'early_season_avg': rookie_early,
            'late_season_avg': rookie_late,
            'adaptation_improvement': rookie_late - rookie_early if not pd.isna(rookie_late) and not pd.isna(rookie_early) else 0
        }
    
    return insights

def calculate_consistency_insights(df: pd.DataFrame) -> Dict:
    """Calcula insights sobre consistência de jogadores"""
    
    insights = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_data = df[df['position'] == position]
        
        # Calcular métricas de consistência por jogador
        player_consistency = pos_data.groupby('player_display_name').agg({
            'fantasy_points_ppr': ['mean', 'std', 'count', 'min', 'max']
        }).reset_index()
        
        player_consistency.columns = ['player', 'avg_points', 'std_points', 'games', 'min_points', 'max_points']
        
        # Filtrar jogadores com pelo menos 16 jogos (uma temporada)
        player_consistency = player_consistency[player_consistency['games'] >= 16]
        
        if not player_consistency.empty:
            # Calcular coeficiente de variação
            player_consistency['cv'] = player_consistency['std_points'] / player_consistency['avg_points']
            
            # Calcular floor e ceiling
            player_consistency['floor'] = player_consistency['avg_points'] - player_consistency['std_points']
            player_consistency['ceiling'] = player_consistency['avg_points'] + player_consistency['std_points']
            
            # Jogadores mais consistentes (menor CV)
            most_consistent = player_consistency.nsmallest(5, 'cv')
            
            # Jogadores com maior upside (maior ceiling)
            highest_ceiling = player_consistency.nlargest(5, 'ceiling')
            
            # Jogadores mais seguros (maior floor)
            highest_floor = player_consistency.nlargest(5, 'floor')
            
            insights[position] = {
                'avg_cv': player_consistency['cv'].mean(),
                'most_consistent': most_consistent,
                'highest_ceiling': highest_ceiling,
                'highest_floor': highest_floor,
                'total_players_analyzed': len(player_consistency)
            }
    
    return insights

def calculate_breakout_insights(df: pd.DataFrame) -> Dict:
    """Calcula insights sobre jogadores breakout"""
    
    # Identificar jogadores com múltiplas temporadas
    player_seasons = df.groupby('player_id')['season'].nunique()
    multi_season_players = player_seasons[player_seasons >= 2].index
    
    multi_season_data = df[df['player_id'].isin(multi_season_players)].copy()
    
    # Calcular performance por temporada do jogador
    player_season_stats = multi_season_data.groupby(['player_id', 'player_display_name', 'position', 'season']).agg({
        'fantasy_points_ppr': 'sum'
    }).reset_index()
    
    # Ordenar por jogador e temporada
    player_season_stats = player_season_stats.sort_values(['player_id', 'season'])
    
    # Calcular mudança year-over-year
    player_season_stats['prev_season_points'] = player_season_stats.groupby('player_id')['fantasy_points_ppr'].shift(1)
    player_season_stats['yoy_change'] = player_season_stats['fantasy_points_ppr'] - player_season_stats['prev_season_points']
    player_season_stats['yoy_change_pct'] = (player_season_stats['yoy_change'] / player_season_stats['prev_season_points']) * 100
    
    # Filtrar apenas mudanças válidas
    valid_changes = player_season_stats.dropna(subset=['yoy_change'])
    
    insights = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_data = valid_changes[valid_changes['position'] == position]
        
        if not pos_data.empty:
            # Maiores breakouts (melhoria > 50 pontos e > 25%)
            breakouts = pos_data[
                (pos_data['yoy_change'] > 50) & 
                (pos_data['yoy_change_pct'] > 25)
            ].nlargest(10, 'yoy_change_pct')
            
            # Maiores quedas
            busts = pos_data[
                (pos_data['yoy_change'] < -50) & 
                (pos_data['yoy_change_pct'] < -25)
            ].nsmallest(10, 'yoy_change_pct')
            
            # Estatísticas gerais
            avg_improvement = pos_data['yoy_change'].mean()
            improvement_std = pos_data['yoy_change'].std()
            
            insights[position] = {
                'breakouts': breakouts,
                'busts': busts,
                'avg_yoy_change': avg_improvement,
                'yoy_volatility': improvement_std,
                'breakout_rate': len(breakouts) / len(pos_data) * 100 if len(pos_data) > 0 else 0,
                'bust_rate': len(busts) / len(pos_data) * 100 if len(pos_data) > 0 else 0
            }
    
    return insights

def calculate_positional_value_insights(df: pd.DataFrame) -> Dict:
    """Calcula insights sobre valor posicional (VBD - Value Based Drafting)"""
    
    insights = {}
    
    # Calcular pontos por temporada para cada jogador
    season_totals = df.groupby(['player_id', 'player_display_name', 'position', 'season']).agg({
        'fantasy_points_ppr': 'sum'
    }).reset_index()
    
    for season in sorted(df['season'].unique()):
        season_data = season_totals[season_totals['season'] == season]
        
        position_insights = {}
        
        for position in ['QB', 'RB', 'WR', 'TE']:
            pos_data = season_data[season_data['position'] == position].sort_values('fantasy_points_ppr', ascending=False)
            
            if not pos_data.empty:
                # Calcular replacement level (jogador #12 para QB, #24 para RB/WR, #12 para TE)
                replacement_ranks = {'QB': 12, 'RB': 24, 'WR': 24, 'TE': 12}
                replacement_rank = replacement_ranks.get(position, 12)
                
                if len(pos_data) >= replacement_rank:
                    replacement_value = pos_data.iloc[replacement_rank - 1]['fantasy_points_ppr']
                else:
                    replacement_value = pos_data.iloc[-1]['fantasy_points_ppr']
                
                # Calcular VBD para top players
                pos_data['vbd'] = pos_data['fantasy_points_ppr'] - replacement_value
                
                # Top 10 por VBD
                top_vbd = pos_data.head(10)
                
                position_insights[position] = {
                    'replacement_value': replacement_value,
                    'top_vbd_players': top_vbd,
                    'position_depth': len(pos_data[pos_data['fantasy_points_ppr'] > replacement_value]),
                    'avg_starter_points': pos_data.head(replacement_rank)['fantasy_points_ppr'].mean(),
                    'scarcity_score': pos_data.head(5)['fantasy_points_ppr'].std()  # Maior std = mais escassez no topo
                }
        
        insights[season] = position_insights
    
    return insights

def calculate_weekly_trends_insights(df: pd.DataFrame) -> Dict:
    """Calcula insights sobre tendências semanais"""
    
    insights = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_data = df[df['position'] == position]
        
        # Tendências por semana da temporada
        weekly_avg = pos_data.groupby('week')['fantasy_points_ppr'].mean()
        
        # Identificar semanas de pico e vale
        peak_week = weekly_avg.idxmax()
        valley_week = weekly_avg.idxmin()
        
        # Tendência geral (correlação com semana)
        correlation = pos_data['week'].corr(pos_data['fantasy_points_ppr'])
        
        # Análise de playoffs (semanas 15-17)
        playoff_weeks = pos_data[pos_data['week'].isin([15, 16, 17])]
        regular_weeks = pos_data[pos_data['week'].isin(range(1, 15))]
        
        playoff_avg = playoff_weeks['fantasy_points_ppr'].mean()
        regular_avg = regular_weeks['fantasy_points_ppr'].mean()
        
        # Jogadores que melhoram nos playoffs
        player_playoff_performance = pos_data.groupby('player_display_name').apply(
            lambda x: x[x['week'].isin([15, 16, 17])]['fantasy_points_ppr'].mean() - 
                     x[x['week'].isin(range(1, 15))]['fantasy_points_ppr'].mean()
        ).sort_values(ascending=False)
        
        insights[position] = {
            'weekly_averages': weekly_avg.to_dict(),
            'peak_week': peak_week,
            'valley_week': valley_week,
            'seasonal_trend': 'increasing' if correlation > 0.1 else 'decreasing' if correlation < -0.1 else 'stable',
            'playoff_boost': playoff_avg - regular_avg,
            'top_playoff_performers': player_playoff_performance.head(5).to_dict()
        }
    
    return insights

def generate_draft_recommendations(df: pd.DataFrame, current_season: int = 2024) -> Dict:
    """Gera recomendações de draft baseadas nos insights"""
    
    # Usar dados das últimas 3 temporadas para projeções
    recent_data = df[df['season'].isin([current_season - 2, current_season - 1, current_season])]
    
    recommendations = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_data = recent_data[recent_data['position'] == position]
        
        # Calcular métricas agregadas por jogador
        player_metrics = pos_data.groupby('player_display_name').agg({
            'fantasy_points_ppr': ['mean', 'std', 'sum'],
            'season': 'count'
        }).reset_index()
        
        player_metrics.columns = ['player', 'avg_ppg', 'std_ppg', 'total_points', 'seasons_played']
        
        # Filtrar jogadores com pelo menos 2 temporadas
        experienced_players = player_metrics[player_metrics['seasons_played'] >= 2]
        
        if not experienced_players.empty:
            # Calcular score composto (média ponderada por consistência)
            experienced_players['consistency_score'] = experienced_players['avg_ppg'] / (experienced_players['std_ppg'] + 1)
            experienced_players['draft_score'] = (experienced_players['avg_ppg'] * 0.7) + (experienced_players['consistency_score'] * 0.3)
            
            # Top recomendações
            top_safe_picks = experienced_players.nlargest(5, 'consistency_score')
            top_upside_picks = experienced_players.nlargest(5, 'avg_ppg')
            top_overall = experienced_players.nlargest(10, 'draft_score')
            
            recommendations[position] = {
                'safe_picks': top_safe_picks[['player', 'avg_ppg', 'std_ppg', 'consistency_score']].to_dict('records'),
                'upside_picks': top_upside_picks[['player', 'avg_ppg', 'total_points']].to_dict('records'),
                'overall_rankings': top_overall[['player', 'draft_score', 'avg_ppg']].to_dict('records')
            }
    
    return recommendations

def display_insights_summary(df: pd.DataFrame):
    """Exibe resumo dos principais insights"""
    
    st.markdown("### 🧠 Principais Insights")
    
    # Calcular insights
    rookie_insights = calculate_rookie_insights(df)
    consistency_insights = calculate_consistency_insights(df)
    breakout_insights = calculate_breakout_insights(df)
    
    # Criar tabs para diferentes tipos de insights
    insight_tab1, insight_tab2, insight_tab3, insight_tab4 = st.tabs([
        "🆕 Rookies", "📊 Consistência", "🚀 Breakouts", "💎 Valor Posicional"
    ])
    
    with insight_tab1:
        st.markdown("#### Análise de Performance de Rookies")
        
        for position in ['QB', 'RB', 'WR', 'TE']:
            if position in rookie_insights:
                insights = rookie_insights[position]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**{position}**")
                    st.metric(
                        "Gap Veterano-Rookie", 
                        f"{insights['performance_gap']:.1f} pts",
                        f"{insights['gap_percentage']:.1f}%"
                    )
                    
                    if insights['adaptation_improvement'] > 0:
                        st.success(f"📈 Rookies melhoram {insights['adaptation_improvement']:.1f} pts após semana 4")
                    else:
                        st.warning(f"📉 Rookies pioram {abs(insights['adaptation_improvement']):.1f} pts após semana 4")
                
                with col2:
                    if not insights['top_rookies'].empty:
                        st.markdown("**Top Rookies Históricos:**")
                        for _, rookie in insights['top_rookies'].head(3).iterrows():
                            st.write(f"• {rookie['player_display_name']} ({rookie['rookie_season']}): {rookie['fantasy_points_ppr']:.1f} pts")
    
    with insight_tab2:
        st.markdown("#### Análise de Consistência")
        
        for position in ['QB', 'RB', 'WR', 'TE']:
            if position in consistency_insights:
                insights = consistency_insights[position]
                
                st.markdown(f"**{position}** - CV Médio: {insights['avg_cv']:.3f}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Mais Consistentes:**")
                    for _, player in insights['most_consistent'].head(3).iterrows():
                        st.write(f"• {player['player']} (CV: {player['cv']:.3f})")
                
                with col2:
                    st.markdown("**Maior Ceiling:**")
                    for _, player in insights['highest_ceiling'].head(3).iterrows():
                        st.write(f"• {player['player']} ({player['ceiling']:.1f} pts)")
                
                with col3:
                    st.markdown("**Maior Floor:**")
                    for _, player in insights['highest_floor'].head(3).iterrows():
                        st.write(f"• {player['player']} ({player['floor']:.1f} pts)")
    
    with insight_tab3:
        st.markdown("#### Análise de Breakouts e Busts")
        
        for position in ['QB', 'RB', 'WR', 'TE']:
            if position in breakout_insights:
                insights = breakout_insights[position]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**{position} - Maiores Breakouts:**")
                    if not insights['breakouts'].empty:
                        for _, player in insights['breakouts'].head(3).iterrows():
                            st.success(f"📈 {player['player_display_name']} ({player['season']}): +{player['yoy_change_pct']:.1f}%")
                    else:
                        st.info("Nenhum breakout significativo encontrado")
                
                with col2:
                    st.markdown(f"**{position} - Maiores Quedas:**")
                    if not insights['busts'].empty:
                        for _, player in insights['busts'].head(3).iterrows():
                            st.error(f"📉 {player['player_display_name']} ({player['season']}): {player['yoy_change_pct']:.1f}%")
                    else:
                        st.info("Nenhuma queda significativa encontrada")
                
                # Estatísticas gerais
                st.info(f"Taxa de Breakout: {insights['breakout_rate']:.1f}% | Taxa de Bust: {insights['bust_rate']:.1f}%")
    
    with insight_tab4:
        st.markdown("#### Análise de Valor Posicional")
        st.info("🚧 Análise VBD em desenvolvimento - será implementada na próxima versão")

def create_advanced_filters():
    """Cria filtros avançados para análises específicas"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔬 Filtros Avançados")
    
    # Filtro de experiência
    experience_filter = st.sidebar.selectbox(
        "👶 Experiência",
        options=['Todos', 'Apenas Rookies', 'Apenas Veteranos (2+ anos)', 'Veteranos Experientes (5+ anos)'],
        help="Filtrar por nível de experiência do jogador"
    )
    
    # Filtro de performance
    performance_filter = st.sidebar.selectbox(
        "⭐ Nível de Performance",
        options=['Todos', 'Elite (Top 5)', 'Starter (Top 12/24)', 'Flex (Top 36)', 'Bench (Resto)'],
        help="Filtrar por nível de performance fantasy"
    )
    
    # Filtro de consistência
    consistency_filter = st.sidebar.selectbox(
        "📊 Consistência",
        options=['Todos', 'Muito Consistente (CV < 0.5)', 'Consistente (CV < 0.8)', 'Volátil (CV > 0.8)'],
        help="Filtrar por nível de consistência"
    )
    
    return {
        'experience': experience_filter,
        'performance': performance_filter,
        'consistency': consistency_filter
    }
