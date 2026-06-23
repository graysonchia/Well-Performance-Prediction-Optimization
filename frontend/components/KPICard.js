import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../constants/theme';

export function KPICard({ label, value, unit = '', icon, color = colors.orange, trend = null }) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        {icon && <Ionicons name={icon} size={24} color={color} style={styles.icon} />}
        <Text style={styles.label}>{label}</Text>
      </View>
      <View style={styles.content}>
        <Text style={[styles.value, { color }]}>
          {typeof value === 'number' ? value.toFixed(1) : value}
        </Text>
        {unit && <Text style={styles.unit}>{unit}</Text>}
      </View>
      {trend && (
        <Text style={[styles.trend, { color: trend.value >= 0 ? colors.success : colors.red }]}>
          {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value).toFixed(1)}%
        </Text>
      )}
    </View>
  );
}

export function KPIGrid({ children }) {
  return <View style={styles.grid}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 100,
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    justifyContent: 'space-between',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  icon: {
    marginRight: 6,
  },
  label: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  content: {
    marginBottom: 6,
  },
  value: {
    fontSize: 20,
    fontWeight: '800',
  },
  unit: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  trend: {
    fontSize: 11,
    fontWeight: '700',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
});
