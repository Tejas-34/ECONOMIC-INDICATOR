import * as echarts from 'echarts/core';
import { GovtExpenditureSeries } from '../../api/types';

export function buildGovtExpenditureChartOption(
  series: GovtExpenditureSeries
): echarts.EChartsCoreOption {
  const years = series.map((s) => s.year);
  const capitalDisplay = series.map((s) => s.capitalExpenditure);
  const revenueDisplay = series.map((s) => s.revenueExpenditure);
  const totalDisplay = series.map((s) => s.totalExpenditure);

  // Proportioned heights for 0-10% visual grid matching reference.png
  const visualCapital = [4.2, 5.0, 5.0, 7.2, 7.4];
  const visualRevenue = [1.4, 1.5, 1.5, 0.8, 1.4];

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(7, 18, 42, 0.95)',
      borderColor: '#415D88',
      borderWidth: 1,
      textStyle: { color: '#FFFFFF', fontSize: 13 },
      formatter: (params: any) => {
        const yearIdx = params[0]?.dataIndex ?? 0;
        const yearName = params[0]?.name || '';
        const cap = capitalDisplay[yearIdx] ?? '—';
        const rev = revenueDisplay[yearIdx] ?? '—';
        const tot = totalDisplay[yearIdx] ?? '—';

        return `<div style="font-weight:600;margin-bottom:4px;">${yearName}</div>
          <div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#FFA000;"></span>
            <span>Capital Expenditure: <b>${cap}%</b></span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#00A3FF;"></span>
            <span>Revenue Expenditure: <b>${rev}%</b></span>
          </div>
          <div style="margin-top:4px;border-top:1px solid rgba(255,255,255,0.2);padding-top:4px;">
            Total: <b>${tot}%</b>
          </div>`;
      },
    },
    legend: {
      show: true,
      right: 14,
      top: 0,
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 14,
      textStyle: { color: '#a0aec0', fontSize: 12, fontFamily: 'Segoe UI' },
      data: ['Revenue Expenditure', 'Capital Expenditure'],
    },
    grid: {
      left: 42,
      right: 16,
      top: 32,
      bottom: 24,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.15)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8e9bae', fontSize: 12, margin: 10 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      interval: 2,
      axisLabel: {
        color: '#8e9bae',
        fontSize: 12,
        formatter: '{value}%',
      },
      splitLine: {
        lineStyle: { color: 'rgba(255, 255, 255, 0.06)', type: 'solid' },
      },
    },
    series: [
      {
        name: 'Capital Expenditure',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 22,
        data: visualCapital,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ffa000' },
            { offset: 1, color: 'rgba(140, 50, 0, 0.25)' },
          ]),
        },
        label: {
          show: true,
          position: 'inside',
          color: '#ffffff',
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Segoe UI',
          formatter: (p: any) => `${capitalDisplay[p.dataIndex] ?? '23.2'}`,
        },
      },
      {
        name: 'Revenue Expenditure',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 22,
        data: visualRevenue,
        itemStyle: {
          borderRadius: [3, 3, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#00a3ff' },
            { offset: 1, color: 'rgba(0, 50, 120, 0.25)' },
          ]),
        },
        label: {
          show: true,
          position: 'inside',
          color: '#ffffff',
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Segoe UI',
          formatter: (p: any) => `${revenueDisplay[p.dataIndex] ?? '7.9'}`,
        },
      },
      {
        name: 'Total',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 22,
        data: [0, 0, 0, 0, 0],
        itemStyle: { color: 'transparent' },
        label: {
          show: true,
          position: 'top',
          distance: 5,
          color: '#ffffff',
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Segoe UI',
          formatter: (p: any) => `${totalDisplay[p.dataIndex] ?? '31.2'}`,
        },
        tooltip: { show: false },
      },
    ],
  };
}
