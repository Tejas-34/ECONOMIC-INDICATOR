import * as echarts from 'echarts/core';
import { InflationSeries } from '../../api/types';

export function buildInflationChartOption(series: InflationSeries): echarts.EChartsCoreOption {
  const years = series.map((s) => s.year);
  const data = series.map((s) => s.cpiRate);

  return {
    animation: true,
    animationDuration: 300,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#0FCBFF', width: 1 } },
      backgroundColor: 'rgba(7, 18, 42, 0.95)',
      borderColor: '#415D88',
      borderWidth: 1,
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params: any) => {
        const p = params[0];
        const val = p?.value !== null && p?.value !== undefined ? p.value + '%' : '—';
        return `<div style="font-weight:600;margin-bottom:4px;">${p?.name || ''}</div>
                <div style="display:flex;align-items:center;gap:6px;">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#0FCBFF;"></span>
                  <span>Inflation Rate: <b>${val}</b></span>
                </div>`;
      },
    },
    grid: {
      left: 42,
      right: 25,
      top: 32,
      bottom: 26,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: {
        show: true,
        lineStyle: { color: 'rgba(255, 255, 255, 0.15)', width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        show: true,
        color: '#CCCCCC',
        fontSize: 14,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        margin: 12,
      },
      splitLine: {
        show: false,
      },
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
        margin: 10,
      },
      splitLine: {
        show: false,
      },
    },
    series: [
      {
        name: 'Inflation Rate',
        type: 'line',
        smooth: false,
        showSymbol: false,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#00F0FF',
          borderColor: '#FFFFFF',
          borderWidth: 1.5,
        },
        lineStyle: {
          width: 2.5,
          color: '#00F0FF',
          shadowColor: 'rgba(0, 240, 255, 0.45)',
          shadowBlur: 8,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 240, 255, 0.28)' },
            { offset: 0.7, color: 'rgba(0, 240, 255, 0.08)' },
            { offset: 1, color: 'rgba(0, 240, 255, 0.0)' },
          ]),
        },
        markLine: {
          symbol: 'none',
          silent: true,
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.12)',
            width: 1,
            type: 'solid',
          },
          data: [
            { xAxis: '2021' },
            { xAxis: '2022' },
            { xAxis: '2023' },
            { xAxis: '2024' },
            { xAxis: '2025' },
            {
              yAxis: 0,
              lineStyle: {
                color: 'rgba(255, 255, 255, 0.22)',
                width: 1.2,
                type: 'solid',
              },
            },
          ],
          label: { show: false },
        },
        markPoint: {
          symbol: 'roundRect',
          symbolSize: [46, 22],
          symbolOffset: [0, -14],
          itemStyle: {
            color: 'rgba(0, 0, 0, 0.75)',
            borderColor: 'rgba(255, 255, 255, 0.25)',
            borderWidth: 1,
            borderRadius: 10,
          },
          label: {
            show: true,
            color: '#CCCCCC',
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
            formatter: (params: any) => params.value,
          },
          data: series
            .filter((s) => s.cpiRate !== null && s.cpiRate !== undefined)
            .map((s) => ({
              coord: [s.year, s.cpiRate],
              value: s.highlightLabel || `${s.cpiRate}%`,
            })),
        },
        data,
      },
    ],
  };
}
