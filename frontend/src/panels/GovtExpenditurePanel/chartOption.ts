import * as echarts from 'echarts/core';
import { GovtExpenditureSeries } from '../../api/types';

export function buildGovtExpenditureChartOption(
  series: GovtExpenditureSeries
): echarts.EChartsCoreOption {
  const years = series.map((s) => s.year);
  const capitalDisplay = series.map((s) => s.capitalExpenditure);
  const revenueDisplay = series.map((s) => s.revenueExpenditure);
  const totalDisplay = series.map((s) => s.totalExpenditure);

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
        const yearIdx = params[0]?.dataIndex ?? 0;
        const yearName = params[0]?.name || '';
        const cap = capitalDisplay[yearIdx] != null ? `₹${capitalDisplay[yearIdx]}L Cr` : '—';
        const rev = revenueDisplay[yearIdx] != null ? `₹${revenueDisplay[yearIdx]}L Cr` : '—';
        const tot = totalDisplay[yearIdx] != null ? `₹${totalDisplay[yearIdx]}L Cr` : '—';

        return `<div style="font-weight:600;margin-bottom:4px;">${yearName}</div>
          <div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#0FB8E6;"></span>
            <span>Revenue Expenditure: <b>${rev}</b></span>
          </div>
          <div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#FFB012;"></span>
            <span>Capital Expenditure: <b>${cap}</b></span>
          </div>
          <div style="margin-top:4px;border-top:1px solid rgba(255,255,255,0.2);padding-top:4px;">
            Total: <b>${tot}</b>
          </div>`;
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
          name: 'Revenue Expenditure',
          itemStyle: {
            color: '#0FB8E6',
          },
        },
        {
          name: 'Capital Expenditure',
          itemStyle: {
            color: '#FFA73F',
          },
        },
      ],
    },
    grid: {
      left: 56,
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
      splitLine: {
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 60,
      interval: 10,
      axisLine: {
        show: true,
        lineStyle: { color: '#5B5B5B', width: 1 },
      },
      axisTick: { show: false },
      axisLabel: {
        color: '#CCCCCC',
        fontSize: 12,
        fontWeight: 600,
        fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
        formatter: '₹{value}L Cr',
        margin: 8,
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
        name: 'Capital Expenditure',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 32,
        data: capitalDisplay,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#FFB012' },
            { offset: 1, color: '#844B08' },
          ]),
        },
        label: {
          show: true,
          position: 'inside',
          color: '#FFFFFF',
          fontSize: 13,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (p: any) => {
            const val = capitalDisplay[p.dataIndex];
            return val != null ? `${val}` : '';
          },
        },
      },
      {
        name: 'Revenue Expenditure',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 32,
        data: revenueDisplay,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0FB8E6' },
            { offset: 1, color: '#0046B7' },
          ]),
        },
        label: {
          show: true,
          position: 'inside',
          color: '#FFFFFF',
          fontSize: 13,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (p: any) => {
            const val = revenueDisplay[p.dataIndex];
            return val != null ? `${val}` : '';
          },
        },
      },
      {
        name: 'Total',
        type: 'bar',
        stack: 'expenditure',
        barWidth: 32,
        data: series.map(() => 0),
        itemStyle: { color: 'transparent' },
        label: {
          show: true,
          position: 'top',
          distance: 6,
          color: '#FFFFFF',
          fontSize: 14,
          fontWeight: 600,
          fontFamily: 'Segoe UI, Selawik, system-ui, -apple-system, sans-serif',
          formatter: (p: any) => {
            const val = totalDisplay[p.dataIndex];
            return val != null ? `${val}` : '';
          },
        },
        tooltip: { show: false },
      },
    ],
  };
}
