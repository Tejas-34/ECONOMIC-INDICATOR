import * as echarts from 'echarts/core';
import { DebtToGdpSeries } from '../../api/types';

export function buildDebtChartOption(series: DebtToGdpSeries): echarts.EChartsCoreOption {
  const dates = series.map((s) => s.date);
  const data = series.map((s) => s.ratio);

  // MarkPoint data for pill badges at all dates (similar to 2023 style for all years)
  const markPoints = series
    .filter((s) => s.ratio !== null && s.ratio !== undefined)
    .map((s) => ({
      coord: [s.date, s.ratio],
      value: s.highlightLabel || `${s.ratio}%`,
    }));

  return {
    animation: true,
    animationDuration: 300,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#00D2FF', width: 1 } },
      backgroundColor: 'rgba(7, 18, 42, 0.95)',
      borderColor: '#415D88',
      borderWidth: 1,
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params: any) => {
        const p = params[0];
        return `<div style="font-weight:600;margin-bottom:4px;">${p?.name || ''}</div>
                <div style="display:flex;align-items:center;gap:6px;">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#00D2FF;"></span>
                  <span>Debt to GDP: <b>${p?.value !== null ? p?.value + '%' : '—'}</b></span>
                </div>`;
      },
    },
    grid: {
      left: 45,
      right: 30,
      top: 36,
      bottom: 26,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: {
        show: true,
        lineStyle: { color: 'rgba(255, 255, 255, 0.15)', width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        show: true,
        interval: 0,
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
      min: 50,
      max: 100,
      interval: 10,
      axisLine: {
        show: false,
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
          color: 'rgba(255, 255, 255, 0.08)',
          width: 1,
          type: 'solid',
        },
      },
    },
    series: [
      {
        name: 'Debt to GDP Ratio',
        type: 'line',
        smooth: 0.25,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#00D2FF',
          borderColor: '#FFFFFF',
          borderWidth: 1.5,
        },
        lineStyle: {
          color: '#00D2FF',
          width: 2.5,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(15, 203, 255, 0.45)' },
            { offset: 0.65, color: 'rgba(21, 101, 125, 0.18)' },
            { offset: 1, color: 'rgba(21, 101, 125, 0.0)' },
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
          data: dates.map((d) => ({ xAxis: d })),
          label: { show: false },
        },
        markPoint: {
          symbol: 'roundRect',
          symbolSize: [54, 24],
          itemStyle: {
            color: 'rgba(30, 48, 72, 0.85)',
            borderColor: 'rgba(0, 210, 255, 0.45)',
            borderWidth: 1,
            borderRadius: 12,
            shadowColor: 'rgba(0, 0, 0, 0.4)',
            shadowBlur: 6,
          },
          label: {
            show: true,
            color: '#FFFFFF',
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
            formatter: (params: any) => params.value,
          },
          data: markPoints as any,
        },
        data,
      },
    ],
  };
}
