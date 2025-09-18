#!/usr/bin/env python3
"""
Módulo de comparação de jogadores para NFL Fantasy Analytics
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import List, Dict

def create_player_comparison_interface(df: pd.DataFrame):
    """Cria interface para comparação de jogadores"""
    
    st.markdown("### 🆚 Comparação Detalhada de Jogadores")
    
    # Filtros para seleção de jogadores
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por posição primeiro
        position_filter = st.selectbox(
            "🎯 Selecionar Posição:",
            options=['QB', 'RB', 'WR', 'TE'],
            help="Selecione a posição para comparação"
        )
    
    with col2:
        # Filtro por temporadas
        available_seasons = sorted(df['season'].unique(), reverse=True)
        selected_seasons = st.multiselect(
            "📅 Temporadas para Comparação:",
            options=available_seasons,
            default=available_seasons[:3],
            help="Selecione as temporadas para análise"
        )
    
    # Filtrar dados por posição e temporadas
    filtered_data = df[
        (df['position'] == position_filter) & 
        (df['season'].isin(selected_seasons))
    ]
    
    if filtered_data.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
        return
    
    # Calcular estatísticas agregadas por jogador
    player_stats = filtered_data.groupby('player_display_name').agg({
        'fantasy_points_ppr': ['sum', 'mean', 'std', 'count'],
        'recent_team': 'last'
    }).reset_index()
    
    player_stats.columns = ['player', 'total_points', 'avg_points', 'std_points', 'games', 'team']
    
    # Filtrar jogadores com pelo menos 8 jogos
    player_stats = player_stats[player_stats['games'] >= 8]
    
    # Ordenar por total de pontos
    player_stats = player_stats.sort_values('total_points', ascending=False)
    
    # Seleção de jogadores para comparação
    st.markdown("#### 👥 Selecionar Jogadores para Comparação")
    
    # Criar opções de jogadores com informações
    player_options = [
        f"{row['player']} ({row['team']}) - {row['total_points']:.0f} pts, {row['games']} jogos"
        for _, row in player_stats.head(50).iterrows()
    ]
    
    selected_players = st.multiselect(
        "🔍 Escolher Jogadores (máximo 5):",
        options=player_options,
        default=player_options[:3] if len(player_options) >= 3 else player_options,
        help="Selecione até 5 jogadores para comparação detalhada"
    )
    
    if len(selected_players) < 2:
        st.info("ℹ️ Selecione pelo menos 2 jogadores para comparação.")
        return
    
    if len(selected_players) > 5:
        st.warning("⚠️ Máximo de 5 jogadores permitido. Usando os primeiros 5 selecionados.")
        selected_players = selected_players[:5]
    
    # Extrair nomes dos jogadores selecionados
    player_names = [player.split(' (')[0] for player in selected_players]
    
    # Filtrar dados dos jogadores selecionados
    comparison_data = filtered_data[filtered_data['player_display_name'].isin(player_names)]
    
    # Criar visualizações de comparação
    create_comparison_visualizations(comparison_data, player_names, position_filter)
    
    # Criar tabela de estatísticas comparativas
    create_comparison_table(comparison_data, player_names)

def create_comparison_visualizations(df: pd.DataFrame, players: List[str], position: str):
    """Cria visualizações para comparação de jogadores"""
    
    st.markdown("#### 📊 Visualizações Comparativas")
    
    # Tab para diferentes tipos de comparação
    comp_tab1, comp_tab2, comp_tab3, comp_tab4 = st.tabs([
        "📈 Performance Temporal", "📊 Estatísticas Médias", "🎯 Consistência", "📋 Head-to-Head"
    ])
    
    with comp_tab1:
        create_temporal_comparison(df, players)
    
    with comp_tab2:
        create_stats_comparison(df, players, position)
    
    with comp_tab3:
        create_consistency_comparison(df, players)
    
    with comp_tab4:
        create_head_to_head_comparison(df, players)

def create_temporal_comparison(df: pd.DataFrame, players: List[str]):
    """Cria gráfico de comparação temporal"""
    
    st.markdown("##### 📈 Performance ao Longo do Tempo")
    
    # Preparar dados por semana/temporada
    temporal_data = df.groupby(['player_display_name', 'season', 'week']).agg({
        'fantasy_points_ppr': 'sum'
    }).reset_index()
    
    # Criar coluna de identificação temporal
    temporal_data['game_id'] = temporal_data['season'].astype(str) + '-W' + temporal_data['week'].astype(str)
    
    # Gráfico de linha temporal
    fig = go.Figure()
    
    colors = ['#e74c3c', '#3498db', '#f1c40f', '#27ae60', '#9b59b6']
    
    for i, player in enumerate(players):
        player_data = temporal_data[temporal_data['player_display_name'] == player]
        
        fig.add_trace(go.Scatter(
            x=list(range(len(player_data))),
            y=player_data['fantasy_points_ppr'],
            mode='lines+markers',
            name=player,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=4),
            hovertemplate=f'<b>{player}</b><br>' +
                         'Jogo: %{x}<br>' +
                         'Fantasy Points: %{y:.1f}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title="Fantasy Points PPR por Jogo",
        xaxis_title="Jogos (Cronológico)",
        yaxis_title="Fantasy Points PPR",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de média móvel
    st.markdown("##### 📊 Média Móvel (5 jogos)")
    
    fig_ma = go.Figure()
    
    for i, player in enumerate(players):
        player_data = temporal_data[temporal_data['player_display_name'] == player].sort_values(['season', 'week'])
        
        # Calcular média móvel
        player_data['moving_avg'] = player_data['fantasy_points_ppr'].rolling(window=5, min_periods=1).mean()
        
        fig_ma.add_trace(go.Scatter(
            x=list(range(len(player_data))),
            y=player_data['moving_avg'],
            mode='lines',
            name=f"{player} (MA5)",
            line=dict(color=colors[i % len(colors)], width=3),
            hovertemplate=f'<b>{player}</b><br>' +
                         'Média Móvel: %{y:.1f}<br>' +
                         '<extra></extra>'
        ))
    
    fig_ma.update_layout(
        title="Média Móvel de Fantasy Points (5 jogos)",
        xaxis_title="Jogos (Cronológico)",
        yaxis_title="Fantasy Points PPR (Média Móvel)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig_ma, use_container_width=True)

def create_stats_comparison(df: pd.DataFrame, players: List[str], position: str):
    """Cria comparação de estatísticas médias"""
    
    st.markdown("##### 📊 Comparação de Estatísticas Médias")
    
    # Definir métricas relevantes por posição
    position_metrics = {
        'QB': ['fantasy_points_ppr', 'passing_yards', 'passing_tds', 'interceptions', 'rushing_yards'],
        'RB': ['fantasy_points_ppr', 'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards'],
        'WR': ['fantasy_points_ppr', 'receptions', 'receiving_yards', 'receiving_tds', 'targets'],
        'TE': ['fantasy_points_ppr', 'receptions', 'receiving_yards', 'receiving_tds', 'targets']
    }
    
    metrics = position_metrics.get(position, ['fantasy_points_ppr'])
    
    # Calcular médias por jogador
    player_averages = df.groupby('player_display_name')[metrics].mean().reset_index()
    player_averages = player_averages[player_averages['player_display_name'].isin(players)]
    
    # Criar gráfico de radar
    fig = go.Figure()
    
    colors = ['#e74c3c', '#3498db', '#f1c40f', '#27ae60', '#9b59b6']
    
    for i, player in enumerate(players):
        player_data = player_averages[player_averages['player_display_name'] == player]
        
        if not player_data.empty:
            values = [player_data[metric].iloc[0] for metric in metrics]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics,
                fill='toself',
                name=player,
                line_color=colors[i % len(colors)],
                opacity=0.6
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max([player_averages[metric].max() for metric in metrics])]
            )
        ),
        title="Comparação de Estatísticas (Gráfico Radar)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de barras comparativo
    st.markdown("##### 📊 Comparação por Métrica")
    
    selected_metric = st.selectbox(
        "Selecionar Métrica:",
        options=metrics,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    fig_bar = px.bar(
        player_averages,
        x='player_display_name',
        y=selected_metric,
        title=f"Comparação: {selected_metric.replace('_', ' ').title()}",
        color='player_display_name',
        color_discrete_sequence=colors
    )
    
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

def create_consistency_comparison(df: pd.DataFrame, players: List[str]):
    """Cria comparação de consistência"""
    
    st.markdown("##### 🎯 Análise de Consistência")
    
    # Calcular métricas de consistência
    consistency_data = df.groupby('player_display_name').agg({
        'fantasy_points_ppr': ['mean', 'std', 'min', 'max', 'count']
    }).reset_index()
    
    consistency_data.columns = ['player', 'avg', 'std', 'min', 'max', 'games']
    consistency_data = consistency_data[consistency_data['player'].isin(players)]
    
    # Calcular métricas adicionais
    consistency_data['cv'] = consistency_data['std'] / consistency_data['avg']  # Coeficiente de variação
    consistency_data['floor'] = consistency_data['avg'] - consistency_data['std']
    consistency_data['ceiling'] = consistency_data['avg'] + consistency_data['std']
    
    # Gráfico de dispersão: Média vs Consistência
    fig_scatter = px.scatter(
        consistency_data,
        x='avg',
        y='cv',
        size='games',
        color='player',
        title="Performance vs Consistência",
        labels={
            'avg': 'Média Fantasy Points PPR',
            'cv': 'Coeficiente de Variação (menor = mais consistente)'
        },
        hover_data=['min', 'max', 'games']
    )
    
    fig_scatter.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Gráfico de floor vs ceiling
    fig_range = go.Figure()
    
    colors = ['#e74c3c', '#3498db', '#f1c40f', '#27ae60', '#9b59b6']
    
    for i, player in enumerate(players):
        player_data = consistency_data[consistency_data['player'] == player]
        
        if not player_data.empty:
            row = player_data.iloc[0]
            
            # Barra do floor ao ceiling
            fig_range.add_trace(go.Scatter(
                x=[row['floor'], row['ceiling']],
                y=[player, player],
                mode='lines+markers',
                name=f"{player} Range",
                line=dict(color=colors[i % len(colors)], width=8),
                marker=dict(size=8),
                showlegend=False
            ))
            
            # Ponto da média
            fig_range.add_trace(go.Scatter(
                x=[row['avg']],
                y=[player],
                mode='markers',
                name=f"{player} Média",
                marker=dict(
                    size=12,
                    color='white',
                    line=dict(color=colors[i % len(colors)], width=2)
                ),
                showlegend=False
            ))
    
    fig_range.update_layout(
        title="Floor, Ceiling e Média por Jogador",
        xaxis_title="Fantasy Points PPR",
        yaxis_title="Jogadores",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    st.plotly_chart(fig_range, use_container_width=True)

def create_head_to_head_comparison(df: pd.DataFrame, players: List[str]):
    """Cria comparação head-to-head"""
    
    st.markdown("##### 📋 Comparação Head-to-Head")
    
    # Calcular estatísticas detalhadas
    detailed_stats = df.groupby('player_display_name').agg({
        'fantasy_points_ppr': ['sum', 'mean', 'std', 'min', 'max', 'count'],
        'season': ['min', 'max']
    }).reset_index()
    
    # Flatten column names
    detailed_stats.columns = [
        'player', 'total_points', 'avg_points', 'std_points', 'min_points', 
        'max_points', 'games', 'first_season', 'last_season'
    ]
    
    detailed_stats = detailed_stats[detailed_stats['player'].isin(players)]
    
    # Calcular métricas adicionais
    detailed_stats['cv'] = detailed_stats['std_points'] / detailed_stats['avg_points']
    detailed_stats['seasons_played'] = detailed_stats['last_season'] - detailed_stats['first_season'] + 1
    detailed_stats['points_per_season'] = detailed_stats['total_points'] / detailed_stats['seasons_played']
    
    # Criar matriz de comparação
    st.markdown("###### 📊 Matriz de Estatísticas")
    
    # Preparar dados para exibição
    display_stats = detailed_stats.copy()
    display_stats = display_stats.round(2)
    
    # Renomear colunas para exibição
    column_mapping = {
        'player': 'Jogador',
        'total_points': 'Total PPR',
        'avg_points': 'Média PPR',
        'std_points': 'Desvio Padrão',
        'min_points': 'Mínimo',
        'max_points': 'Máximo',
        'games': 'Jogos',
        'cv': 'Coef. Variação',
        'seasons_played': 'Temporadas',
        'points_per_season': 'PPR/Temporada'
    }
    
    display_stats = display_stats.rename(columns=column_mapping)
    
    # Destacar o melhor em cada categoria
    st.dataframe(
        display_stats.style.highlight_max(
            subset=['Total PPR', 'Média PPR', 'Máximo', 'PPR/Temporada'],
            color='lightgreen'
        ).highlight_min(
            subset=['Desvio Padrão', 'Mínimo', 'Coef. Variação'],
            color='lightblue'
        ),
        use_container_width=True
    )
    
    # Ranking por categoria
    st.markdown("###### 🏆 Rankings por Categoria")
    
    categories = {
        'Total de Pontos': 'total_points',
        'Média por Jogo': 'avg_points',
        'Consistência (menor CV)': 'cv',
        'Maior Upside (máximo)': 'max_points'
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        for i, (category, column) in enumerate(list(categories.items())[:2]):
            st.markdown(f"**{category}:**")
            
            if column == 'cv':
                ranking = detailed_stats.nsmallest(len(players), column)
            else:
                ranking = detailed_stats.nlargest(len(players), column)
            
            for rank, (_, player) in enumerate(ranking.iterrows(), 1):
                value = player[column]
                st.write(f"{rank}. {player['player']}: {value:.2f}")
    
    with col2:
        for i, (category, column) in enumerate(list(categories.items())[2:]):
            st.markdown(f"**{category}:**")
            
            if column == 'cv':
                ranking = detailed_stats.nsmallest(len(players), column)
            else:
                ranking = detailed_stats.nlargest(len(players), column)
            
            for rank, (_, player) in enumerate(ranking.iterrows(), 1):
                value = player[column]
                st.write(f"{rank}. {player['player']}: {value:.2f}")

def create_comparison_table(df: pd.DataFrame, players: List[str]):
    """Cria tabela detalhada de comparação"""
    
    st.markdown("#### 📋 Tabela Detalhada de Comparação")
    
    # Calcular estatísticas por temporada para cada jogador
    season_stats = df.groupby(['player_display_name', 'season']).agg({
        'fantasy_points_ppr': ['sum', 'mean', 'count'],
        'games': 'sum'
    }).reset_index()
    
    season_stats.columns = ['player', 'season', 'total_points', 'avg_points', 'games']
    season_stats = season_stats[season_stats['player'].isin(players)]
    
    # Pivot para mostrar temporadas como colunas
    pivot_table = season_stats.pivot(index='player', columns='season', values='total_points').fillna(0)
    
    st.dataframe(pivot_table, use_container_width=True)
    
    # Resumo estatístico
    st.markdown("#### 📈 Resumo Estatístico")
    
    summary_stats = df[df['player_display_name'].isin(players)].groupby('player_display_name').agg({
        'fantasy_points_ppr': ['count', 'sum', 'mean', 'std', 'min', 'max'],
    }).round(2)
    
    summary_stats.columns = ['Jogos', 'Total PPR', 'Média PPR', 'Desvio Padrão', 'Mínimo', 'Máximo']
    
    st.dataframe(summary_stats, use_container_width=True)
