/**
 * Chart Components
 *
 * Recharts-based visualization components for the dashboard
 * All charts support:
 * - Responsive sizing
 * - Custom mantis-themed tooltips
 * - Loading states
 * - Accessibility (WCAG 2.1 AA)
 * - Click interactions
 */

export { BaseChart } from './BaseChart';
export { ChartTooltip, SimpleTooltip } from './ChartTooltip';
export { ChartFilters, DateRangeBadge } from './ChartFilters';
export { DonutChart, DonutGauge } from './DonutChart';
export { AreaChart, MiniAreaChart } from './AreaChart';
export { BarChart, MiniBarChart } from './BarChart';
export { TreemapChart, MiniTreemap } from './TreemapChart';
export { TimelineChart, PeakHoursHeatmapStrip } from './TimelineChart';
export { BubbleChart, MiniBubbleChart } from './BubbleChart';
export { BoxPlot, PercentileComparison } from './BoxPlot';
export { StackedAreaChart, SuccessRateTrend } from './StackedAreaChart';
export { RadarChart, MiniRadarChart } from './RadarChart';
export { CircularProgress, MiniCircularProgress } from './CircularProgress';

// Re-exports from recharts for convenience
export {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LineChart,
  Line,
  AreaChart as RechartsAreaChart,
  Area,
  BarChart as RechartsBarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
