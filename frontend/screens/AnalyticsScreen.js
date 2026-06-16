import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

import { chartConfig, colors, spacing } from '../constants/theme';
import api from '../services/api';

const screenWidth = Dimensions.get('window').width;
const chartWidth = screenWidth - spacing.screen * 2;

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function EmptyState({ message }) {
  return (
    <View style={styles.emptyState}>
      <Text style={styles.emptyText}>{message}</Text>
    </View>
  );
}

function downsample(items, maxPoints = 12) {
  if (items.length <= maxPoints) return items;
  const step = Math.ceil(items.length / maxPoints);
  return items.filter((_, index) => index % step === 0).slice(0, maxPoints);
}

function HorizontalBars({ data }) {
  const maxValue = Math.max(...data.map((item) => Number(item.total_downtime_hrs || 0)), 1);

  return (
    <View style={styles.barsCard}>
      {data.map((item) => {
        const value = Number(item.total_downtime_hrs || 0);
        const width = `${Math.max((value / maxValue) * 100, 4)}%`;

        return (
          <View key={item.well_id} style={styles.barRow}>
            <Text style={styles.barLabel} numberOfLines={1}>{item.well_name}</Text>
            <View style={styles.barTrack}>
              <View style={[styles.barFill, { width }]} />
            </View>
            <Text style={styles.barValue}>{Math.round(value)}h</Text>
          </View>
        );
      })}
    </View>
  );
}

export default function AnalyticsScreen() {
  const [wells, setWells] = useState([]);
  const [productionTrend, setProductionTrend] = useState([]);
  const [downtime, setDowntime] = useState([]);
  const [declineCurve, setDeclineCurve] = useState([]);
  const [selectedWellId, setSelectedWellId] = useState(null);
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDecline = useCallback(async (wellId) => {
    if (!wellId) return;
    const response = await api.get(`/analytics/decline-curve/${wellId}`);
    setDeclineCurve(response.data);
  }, []);

  const loadAnalytics = useCallback(async () => {
    setError('');
    try {
      const [wellsRes, trendRes, downtimeRes] = await Promise.all([
        api.get('/wells'),
        api.get('/analytics/production-trend'),
        api.get('/analytics/downtime-summary'),
      ]);
      setWells(wellsRes.data);
      setProductionTrend(trendRes.data);
      setDowntime(downtimeRes.data);

      const initialWellId = selectedWellId || wellsRes.data[0]?.id;
      setSelectedWellId(initialWellId);
      if (initialWellId) {
        await loadDecline(initialWellId);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load analytics.');
    } finally {
      setLoading(false);
    }
  }, [loadDecline, selectedWellId]);

  useFocusEffect(
    useCallback(() => {
      loadAnalytics();
    }, [loadAnalytics])
  );

  const trendChartData = useMemo(() => {
    const totalsByDate = new Map();
    productionTrend.forEach((point) => {
      const date = new Date(point.log_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      totalsByDate.set(date, (totalsByDate.get(date) || 0) + Number(point.total_oil_bbl || 0));
    });
    const points = downsample(Array.from(totalsByDate, ([label, value]) => ({ label, value })));
    return {
      labels: points.map((point) => point.label),
      datasets: [{ data: points.map((point) => Math.round(point.value)) }],
    };
  }, [productionTrend]);

  const declineChartData = useMemo(() => {
    const points = downsample(declineCurve);
    return {
      labels: points.map((point) => new Date(point.log_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
      datasets: [{ data: points.map((point) => Number(point.oil_bbl || 0)) }],
    };
  }, [declineCurve]);

  const selectedWell = wells.find((well) => well.id === selectedWellId);

  async function handleSelectWell(wellId) {
    setSelectedWellId(wellId);
    setSelectorOpen(false);
    try {
      await loadDecline(wellId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load decline curve.');
    }
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.orange} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.screenTitle}>Analytics</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Section title="Production Trend by Field">
        {productionTrend.length ? (
          <LineChart
            data={trendChartData}
            width={chartWidth}
            height={240}
            chartConfig={chartConfig}
            style={styles.chart}
            bezier
            fromZero
          />
        ) : (
          <EmptyState message="No production trend data available." />
        )}
      </Section>

      <Section title="Downtime Summary per Well">
        {downtime.length ? (
          <HorizontalBars data={downtime.slice(0, 10)} />
        ) : (
          <EmptyState message="No downtime data available." />
        )}
      </Section>

      <Section title="Decline Curve">
        <Pressable onPress={() => setSelectorOpen((open) => !open)} style={styles.selector}>
          <Text style={styles.selectorText}>{selectedWell?.well_name || 'Select well'}</Text>
          <Ionicons name={selectorOpen ? 'chevron-up' : 'chevron-down'} size={20} color={colors.orange} />
        </Pressable>

        {selectorOpen ? (
          <View style={styles.selectorMenu}>
            {wells.map((well) => (
              <Pressable key={well.id} onPress={() => handleSelectWell(well.id)} style={styles.selectorItem}>
                <Text style={styles.selectorItemText}>{well.well_name}</Text>
                <Text style={styles.selectorItemMeta}>{well.field_name}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}

        {declineCurve.length ? (
          <LineChart
            data={declineChartData}
            width={chartWidth}
            height={240}
            chartConfig={chartConfig}
            style={styles.chart}
            bezier
            fromZero
          />
        ) : (
          <EmptyState message="Select a well to view decline curve data." />
        )}
      </Section>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.screen,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  screenTitle: {
    color: colors.white,
    fontSize: 24,
    fontWeight: '800',
    marginBottom: 16,
  },
  section: {
    marginBottom: 18,
  },
  sectionTitle: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 10,
  },
  chart: {
    borderRadius: 8,
  },
  barsCard: {
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    gap: 12,
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  barLabel: {
    width: 72,
    color: colors.white,
    fontSize: 12,
    fontWeight: '700',
  },
  barTrack: {
    flex: 1,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.navy,
    overflow: 'hidden',
  },
  barFill: {
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.orange,
  },
  barValue: {
    width: 48,
    textAlign: 'right',
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
  },
  selector: {
    height: 48,
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  selectorText: {
    color: colors.white,
    fontWeight: '800',
  },
  selectorMenu: {
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 12,
    overflow: 'hidden',
  },
  selectorItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  selectorItemText: {
    color: colors.white,
    fontWeight: '800',
  },
  selectorItemMeta: {
    color: colors.muted,
    marginTop: 2,
    fontSize: 12,
  },
  emptyState: {
    minHeight: 140,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyText: {
    color: colors.muted,
  },
  error: {
    color: colors.red,
    marginBottom: 12,
    fontWeight: '700',
  },
});
