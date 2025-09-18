#!/usr/bin/env python3
"""
Módulo de visualizações avançadas para NFL Fantasy Analytics
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Optional

# Paleta de cores baseada no design de referência
COLORS = {
    'primary': '#e74c3c',
    'secondary': '#3498db', 
    'accent': '#f1c40f',
    'dark_blue': '#1e3a5f',
    'light_blue': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c'
}

def create_player_timeline_chart(player_data: pd.DataFrame, metric: str = 'fantasy_points_ppr'):
    """Cria gráfico de linha temporal do jogador similar ao design de referência"""
    
    # Preparar dados por temporada
    season_data = player_data.groupby('season').agg({
        metric: 'mean',
        'week': 'count'  # Usar 'week' em vez de 'games' que não existe
    }).reset_index()
    season_data.columns = ['season', metric, 'games']
    
    fig = go.Figure()
    
    # Linha principal
    fig.add_trace(go.Scatter(
        x=season_data['season'],
        y=season_data[metric],
        mode='lines+markers',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=8, color=COLORS['primary']),
        name=metric.replace('_', ' ').title(),
        hovertemplate='<b>%{x}</b><br>' + 
                     f'{metric.replace("_", " ").title()}: %{{y:.1f}}<br>' +
                     '<extra></extra>'
    ))
    
    # Adicionar anotações nos pontos
    for _, row in season_data.iterrows():
        fig.add_annotation(
            x=row['season'],
            y=row[metric],
            text=f"{row[metric]:.1f}",
            showarrow=False,
            yshift=15,
            font=dict(color='white', size=10)
        )
    
    fig.update_layout(
        title=f"{metric.replace('_', ' ').title()} por Temporada",
        xaxis_title="Temporada",
        yaxis_title=metric.replace('_', ' ').title(),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        showlegend=False,
        height=400
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    return fig

def create_dual_bar_chart(player_data: pd.DataFrame, metric1: str, metric2: str):
    """Cria gráfico de barras duplas similar ao design de referência"""
    
    # Preparar dados por temporada
    season_data = player_data.groupby('season').agg({
        metric1: 'sum',
        metric2: 'sum'
    }).reset_index()
    
    fig = go.Figure()
    
    # Barras do primeiro métrica (vermelho)
    fig.add_trace(go.Bar(
        x=season_data['season'],
        y=season_data[metric1],
        name=metric1.replace('_', ' ').title(),
        marker_color=COLORS['primary'],
        opacity=0.8,
        text=season_data[metric1],
        textposition='inside',
        textfont=dict(color='white', size=10)
    ))
    
    # Barras do segundo métrica (azul)
    fig.add_trace(go.Bar(
        x=season_data['season'],
        y=season_data[metric2],
        name=metric2.replace('_', ' ').title(),
        marker_color=COLORS['secondary'],
        opacity=0.8,
        text=season_data[metric2],
        textposition='inside',
        textfont=dict(color='white', size=10)
    ))
    
    fig.update_layout(
        title=f"{metric1.replace('_', ' ').title()} vs {metric2.replace('_', ' ').title()}",
        xaxis_title="Temporada",
        yaxis_title="Valores",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        barmode='group',
        height=400
    )
    
    return fig

def create_stacked_bar_with_line(player_data: pd.DataFrame):
    """Cria gráfico de barras empilhadas com linha similar ao TD/TO Ratio"""
    
    # Preparar dados por temporada
    season_data = player_data.groupby('season').agg({
        'passing_tds': 'sum',
        'rushing_tds': 'sum',
        'receiving_tds': 'sum',
        'interceptions': 'sum',
        'fumbles_lost': 'sum'
    }).reset_index()
    
    # Calcular TDs totais e TOs totais
    season_data['total_tds'] = (season_data['passing_tds'] + 
                               season_data['rushing_tds'] + 
                               season_data['receiving_tds'])
    
    season_data['total_tos'] = (season_data['interceptions'] + 
                               season_data['fumbles_lost'])
    
    # Calcular ratio (evitar divisão por zero)
    season_data['td_to_ratio'] = np.where(
        season_data['total_tos'] > 0,
        season_data['total_tds'] / season_data['total_tos'],
        season_data['total_tds']
    )
    
    # Criar subplot com eixo Y secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Barras empilhadas para TDs
    fig.add_trace(
        go.Bar(
            x=season_data['season'],
            y=season_data['total_tds'],
            name='Touchdowns',
            marker_color=COLORS['secondary'],
            opacity=0.8,
            text=season_data['total_tds'],
            textposition='inside'
        ),
        secondary_y=False
    )
    
    # Barras empilhadas para TOs
    fig.add_trace(
        go.Bar(
            x=season_data['season'],
            y=season_data['total_tos'],
            name='Turnovers',
            marker_color=COLORS['primary'],
            opacity=0.8,
            text=season_data['total_tos'],
            textposition='inside'
        ),
        secondary_y=False
    )
    
    # Linha para ratio
    fig.add_trace(
        go.Scatter(
            x=season_data['season'],
            y=season_data['td_to_ratio'],
            mode='lines+markers',
            name='TD/TO Ratio',
            line=dict(color=COLORS['accent'], width=3),
            marker=dict(size=8),
            yaxis='y2'
        ),
        secondary_y=True
    )
    
    # Configurar eixos
    fig.update_xaxes(title_text="Temporada")
    fig.update_yaxes(title_text="Touchdowns / Turnovers", secondary_y=False)
    fig.update_yaxes(title_text="TD/TO Ratio", secondary_y=True)
    
    fig.update_layout(
        title="Análise de Touchdowns vs Turnovers",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400,
        barmode='group'
    )
    
    return fig

def create_consistency_chart(df: pd.DataFrame, position: str):
    """Cria gráfico de consistência por posição"""
    
    pos_data = df[df['position'] == position].copy()
    
    # Calcular métricas de consistência por jogador
    consistency_data = pos_data.groupby('player_display_name').agg({
        'fantasy_points_ppr': ['mean', 'std', 'count']
    }).reset_index()
    
    consistency_data.columns = ['player', 'avg_points', 'std_points', 'games']
    
    # Filtrar jogadores com pelo menos 8 jogos
    consistency_data = consistency_data[consistency_data['games'] >= 8]
    
    # Calcular coeficiente de variação (menor = mais consistente)
    consistency_data['cv'] = consistency_data['std_points'] / consistency_data['avg_points']
    
    # Top 20 jogadores por média de pontos
    top_players = consistency_data.nlargest(20, 'avg_points')
    
    fig = go.Figure()
    
    # Scatter plot
    fig.add_trace(go.Scatter(
        x=top_players['avg_points'],
        y=top_players['cv'],
        mode='markers+text',
        marker=dict(
            size=top_players['games'],
            sizemode='diameter',
            sizeref=2.*max(top_players['games'])/(40.**2),
            sizemin=4,
            color=top_players['avg_points'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Média PPR")
        ),
        text=top_players['player'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>' +
                     'Média PPR: %{x:.1f}<br>' +
                     'Coef. Variação: %{y:.2f}<br>' +
                     'Jogos: %{marker.size}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Consistência vs Performance - {position}",
        xaxis_title="Média Fantasy Points PPR",
        yaxis_title="Coeficiente de Variação (menor = mais consistente)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=500
    )
    
    return fig

def create_rookie_analysis_chart(df: pd.DataFrame):
    """Cria análise de performance de rookies vs veteranos"""
    
    # Identificar rookies (primeira temporada de cada jogador)
    player_first_season = df.groupby('player_id')['season'].min().reset_index()
    player_first_season.columns = ['player_id', 'rookie_season']
    
    df_with_rookie = df.merge(player_first_season, on='player_id', how='left')
    df_with_rookie['is_rookie'] = df_with_rookie['season'] == df_with_rookie['rookie_season']
    
    # Análise por posição
    rookie_analysis = df_with_rookie.groupby(['position', 'is_rookie']).agg({
        'fantasy_points_ppr': 'mean'
    }).reset_index()
    
    # Pivot para facilitar visualização
    rookie_pivot = rookie_analysis.pivot(index='position', columns='is_rookie', values='fantasy_points_ppr').reset_index()
    rookie_pivot.columns = ['position', 'veteran_avg', 'rookie_avg']
    
    fig = go.Figure()
    
    # Barras para veteranos
    fig.add_trace(go.Bar(
        x=rookie_pivot['position'],
        y=rookie_pivot['veteran_avg'],
        name='Veteranos',
        marker_color=COLORS['secondary'],
        opacity=0.8
    ))
    
    # Barras para rookies
    fig.add_trace(go.Bar(
        x=rookie_pivot['position'],
        y=rookie_pivot['rookie_avg'],
        name='Rookies',
        marker_color=COLORS['primary'],
        opacity=0.8
    ))
    
    fig.update_layout(
        title="Performance Média: Rookies vs Veteranos por Posição",
        xaxis_title="Posição",
        yaxis_title="Média Fantasy Points PPR",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        barmode='group',
        height=400
    )
    
    return fig

def create_weekly_trends_chart(df: pd.DataFrame, position: str):
    """Cria gráfico de tendências semanais por posição"""
    
    pos_data = df[df['position'] == position].copy()
    
    # Análise por semana da temporada
    weekly_trends = pos_data.groupby('week').agg({
        'fantasy_points_ppr': 'mean'
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=weekly_trends['week'],
        y=weekly_trends['fantasy_points_ppr'],
        mode='lines+markers',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=6, color=COLORS['primary']),
        fill='tonexty',
        fillcolor='rgba(231, 76, 60, 0.1)',
        name=f'{position} Média'
    ))
    
    fig.update_layout(
        title=f"Tendência Semanal - {position}",
        xaxis_title="Semana da Temporada",
        yaxis_title="Média Fantasy Points PPR",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    
    return fig

def create_position_scarcity_chart(df: pd.DataFrame):
    """Cria análise de escassez por posição (posições premium)"""
    
    # Calcular distribuição de pontos por posição
    position_stats = df.groupby('position').agg({
        'fantasy_points_ppr': ['mean', 'std', 'count']
    }).reset_index()
    
    position_stats.columns = ['position', 'avg_points', 'std_points', 'total_games']
    
    # Calcular percentis para análise de escassez
    percentiles = []
    for pos in position_stats['position']:
        pos_data = df[df['position'] == pos]['fantasy_points_ppr']
        percentiles.append({
            'position': pos,
            'p90': pos_data.quantile(0.9),
            'p75': pos_data.quantile(0.75),
            'p50': pos_data.quantile(0.5),
            'p25': pos_data.quantile(0.25),
            'p10': pos_data.quantile(0.1)
        })
    
    percentiles_df = pd.DataFrame(percentiles)
    
    fig = go.Figure()
    
    # Box plot para cada posição
    for pos in percentiles_df['position']:
        pos_data = df[df['position'] == pos]['fantasy_points_ppr']
        
        fig.add_trace(go.Box(
            y=pos_data,
            name=pos,
            boxpoints='outliers',
            marker_color=COLORS['primary'] if pos in ['QB', 'TE'] else COLORS['secondary']
        ))
    
    fig.update_layout(
        title="Distribuição de Fantasy Points por Posição (Análise de Escassez)",
        xaxis_title="Posição",
        yaxis_title="Fantasy Points PPR",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=500
    )
    
    return fig

def create_breakout_analysis_chart(df: pd.DataFrame):
    """Cria análise de jogadores breakout (segunda temporada vs primeira)"""
    
    # Identificar jogadores com pelo menos 2 temporadas
    player_seasons = df.groupby('player_id')['season'].nunique()
    multi_season_players = player_seasons[player_seasons >= 2].index
    
    multi_season_data = df[df['player_id'].isin(multi_season_players)].copy()
    
    # Calcular performance por temporada do jogador
    player_season_rank = multi_season_data.groupby('player_id')['season'].rank(method='dense')
    multi_season_data['player_season_rank'] = player_season_rank
    
    # Comparar primeira vs segunda temporada
    first_second_comparison = multi_season_data[
        multi_season_data['player_season_rank'].isin([1, 2])
    ].groupby(['player_id', 'position', 'player_season_rank']).agg({
        'fantasy_points_ppr': 'mean'
    }).reset_index()
    
    # Pivot para comparação
    comparison_pivot = first_second_comparison.pivot(
        index=['player_id', 'position'], 
        columns='player_season_rank', 
        values='fantasy_points_ppr'
    ).reset_index()
    
    comparison_pivot.columns = ['player_id', 'position', 'first_season', 'second_season']
    comparison_pivot = comparison_pivot.dropna()
    
    # Calcular melhoria
    comparison_pivot['improvement'] = comparison_pivot['second_season'] - comparison_pivot['first_season']
    comparison_pivot['improvement_pct'] = (comparison_pivot['improvement'] / comparison_pivot['first_season']) * 100
    
    fig = go.Figure()
    
    # Scatter plot por posição
    for pos in ['QB', 'RB', 'WR', 'TE']:
        pos_data = comparison_pivot[comparison_pivot['position'] == pos]
        
        if not pos_data.empty:
            fig.add_trace(go.Scatter(
                x=pos_data['first_season'],
                y=pos_data['second_season'],
                mode='markers',
                name=pos,
                marker=dict(size=8, opacity=0.7),
                hovertemplate=f'<b>{pos}</b><br>' +
                             'Primeira Temporada: %{x:.1f}<br>' +
                             'Segunda Temporada: %{y:.1f}<br>' +
                             '<extra></extra>'
            ))
    
    # Linha de referência (sem melhoria)
    max_val = max(comparison_pivot['first_season'].max(), comparison_pivot['second_season'].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        name='Sem Melhoria',
        line=dict(dash='dash', color='white', width=1),
        showlegend=False
    ))
    
    fig.update_layout(
        title="Análise de Breakout: Primeira vs Segunda Temporada",
        xaxis_title="Fantasy Points PPR - Primeira Temporada",
        yaxis_title="Fantasy Points PPR - Segunda Temporada",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=500
    )
    
    return fig
