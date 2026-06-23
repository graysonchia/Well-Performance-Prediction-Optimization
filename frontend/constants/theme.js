export const colors = {
  navy: '#0a1628',
  navy2: '#10233d',
  background: '#07111f',
  card: '#12243b',
  orange: '#f5a623',
  orangeDark: '#c67b08',
  white: '#ffffff',
  muted: '#94a3b8',
  border: '#24364f',
  green: '#2ecc71',
  red: '#e74c3c',
  yellow: '#f1c40f',
  blue: '#4aa3ff',
  cyan: '#3dd5f3',
  purple: '#a78bfa',
  success: '#10b981',
};

export const chartConfig = {
  backgroundGradientFrom: colors.card,
  backgroundGradientTo: colors.card,
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(245, 166, 35, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
  propsForDots: {
    r: '3',
    strokeWidth: '1',
    stroke: colors.orange,
  },
  propsForBackgroundLines: {
    stroke: colors.border,
  },
  barPercentage: 0.62,
};

export const spacing = {
  screen: 16,
  cardRadius: 8,
};
