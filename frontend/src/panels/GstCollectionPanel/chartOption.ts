import * as echarts from 'echarts/core';
import { GstCollectionSeries } from '../../api/types';

export function buildGstChartOption(series: GstCollectionSeries): echarts.EChartsCoreOption {
  const years = series.map((s) => s.year);
  const collections = series.map((s) => s.collectionRate);
  const averages = series.map((s) => s.averageRate);

  return {
    animation: true,
    animationDuration: 300,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { color: 'rgba(255, 255, 255, 0.2)' } },
      backgroundColor: 'rgba(7, 18, 42, 0.95)',
      borderColor: '#415D88',
      borderWidth: 1,
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params: any) => {
        let content = `<div style="font-weight:600;margin-bottom:4px;">${params[0]?.name || ''}</div>`;
        params.forEach((p: any) => {
          const color = p.seriesName === 'Imports' ? '#0FB8E6' : '#F4E15C';
          content += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${color};"></span>
            <span>${p.seriesName}: <b>${p.value !== null ? p.value + '%' : '—'}</b></span>
          </div>`;
        });
        return content;
      },
    },
    legend: {
      show: true,
      right: 20,
      top: 4,
      itemWidth: 22,
      itemHeight: 12,
      itemGap: 18,
      textStyle: {
        color: '#CCCCCC',
        fontSize: 14,
        fontWeight: 500,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
      },
      data: [
        { name: 'Imports', icon: 'roundRect' },
        { name: 'Trade Balance' },
      ],
    },
    grid: {
      left: 45,
      right: 20,
      top: 36,
      bottom: 24,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.15)', width: 1 } },
      axisTick: { show: false },
      axisLabel: {
        color: '#CCCCCC',
        fontSize: 14,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        margin: 12,
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      interval: 2,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#CCCCCC',
        fontSize: 14,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        formatter: '{value}%',
        margin: 12,
      },
      splitLine: {
        show: true,
        lineStyle: { color: 'rgba(255, 255, 255, 0.08)', type: 'solid', width: 1 },
      },
    },
    series: [
      {
        name: 'Imports',
        type: 'bar',
        barWidth: 28,
        data: collections,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0FB8E6' },
            { offset: 0.5, color: '#0278A6' },
            { offset: 1, color: '#061E44' },
          ]),
        },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#CCCCCC',
          fontSize: 13,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (params: any) =>
            params.value !== null && params.value !== undefined ? `${params.value}%` : '',
        },
      },
      {
        name: 'Trade Balance',
        type: 'line',
        smooth: false,
        data: averages,
        lineStyle: { color: '#F4E15C', width: 2.5, cap: 'round', join: 'round' },
        itemStyle: { color: '#F4E15C', borderColor: '#F4E15C', borderWidth: 1 },
        symbol: 'circle',
        symbolSize: 9,
        label: {
          show: true,
          position: 'bottom',
          distance: 8,
          backgroundColor: 'rgba(10, 20, 35, 0.75)',
          borderColor: 'rgba(255, 255, 255, 0.22)',
          borderWidth: 1,
          borderRadius: 10,
          padding: [3, 8],
          color: '#CCCCCC',
          fontSize: 12,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (params: any) => {
            const item = series[params.dataIndex];
            if (item?.highlightLabel) return item.highlightLabel;
            if (params.value !== null && params.value !== undefined) return `${params.value}%`;
            return '—';
          },
        },
      },
    ],
  };
}
