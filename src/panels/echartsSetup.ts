import * as echarts from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkPointComponent,
  MarkLineComponent,
  GraphicComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkPointComponent,
  MarkLineComponent,
  GraphicComponent,
  CanvasRenderer,
]);

export { echarts };
