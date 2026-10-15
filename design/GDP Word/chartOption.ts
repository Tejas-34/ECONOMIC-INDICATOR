import * as echarts from 'echarts/core';
import { GdpGrowthSeries } from '../../api/types';

export function buildGdpChartOption(series: GdpGrowthSeries): echarts.EChartsCoreOption {
  const years = series.map((item) => item.year);
  const indiaData = series.map((item) => item.indiaRate);
  const worldData = series.map((item) => item.worldRate);

  return {
    animation: true,
    animationDuration: 300,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(7, 18, 42, 0.95)',
      borderColor: '#415D88',
      borderWidth: 1,
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params: any) => {
        let content = `<div style="font-weight:600;margin-bottom:4px;">${params[0]?.name || ''}</div>`;
        params.forEach((p: any) => {
          content += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${
              p.color?.colorStops ? p.color.colorStops[0].color : p.color
            };"></span>
            <span>${p.seriesName}: <b>${p.value !== null ? p.value + '%' : '—'}</b></span>
          </div>`;
        });
        return content;
      },
    },
    legend: {
      show: true,
      right: 25,
      top: 4,
      icon: 'roundRect',
      itemWidth: 15,
      itemHeight: 15,
      itemGap: 18,
      textStyle: {
        color: '#CCCCCC',
        fontSize: 15,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
      },
      data: [
        {
          name: 'India',
          itemStyle: {
            color: '#0FB8E6',
          },
        },
        {
          name: 'World',
          itemStyle: {
            color: '#FFB012',
          },
        },
      ],
    },
    grid: {
      left: 48,
      right: 25,
      top: 36,
      bottom: 26,
      show: true,
      borderWidth: 1,
      borderColor: '#5B5B5B',
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: {
        show: true,
        lineStyle: { color: '#5B5B5B', width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#CCCCCC',
        fontSize: 15,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        margin: 12,
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      interval: 2,
      axisLine: {
        show: true,
        lineStyle: { color: '#5B5B5B', width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#CCCCCC',
        fontSize: 14,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        formatter: '{value}%',
        margin: 10,
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: '#5B5B5B',
          width: 1,
          type: 'solid',
        },
      },
    },
    series: [
      {
        name: 'India',
        type: 'bar',
        barWidth: 25.4,
        barGap: '24%',
        data: indiaData,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0FB8E6' },
            { offset: 1, color: '#061E44' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#CCCCCC',
          fontSize: 14,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (params: any) => (params.value !== null ? `${params.value}%` : '—'),
        },
      },
      {
        name: 'World',
        type: 'bar',
        barWidth: 25.4,
        data: worldData,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#FFB012' },
            { offset: 1, color: '#844B08' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#CCCCCC',
          fontSize: 14,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (params: any) => (params.value !== null ? `${params.value}%` : '—'),
        },
      },
    ],
  };
}
