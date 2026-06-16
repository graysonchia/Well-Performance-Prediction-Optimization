import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

import { chartConfig, colors, spacing } from '../constants/theme';
import api from '../services/api';

const screenWidth = Dimensions.get('window').width;
const chartWidth = screenWidth - spacing.screen * 2;

function StatCard({ label, value, icon }) {
  return (
    <View style={styles.statCard}>
      <Ionicons name={icon} size={22} color={colors.orange} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function EmptyChart({ message }) {
  return (
    <View style={styles.emptyChart}>
      <Text style={styles.emptyText}>{message}</Text>
    </View>
  );
}

export default function DashboardScreen() {
  const [wells, setWells] = useState([]);
  const [summary, setSummary] = useState([]);
  const [topProducers, setTopProducers] = useState([]);
  const [fieldComparison, setFieldComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const loadDashboard = useCallback(async () => {
    setError('');
    try {
      const [wellsRes, summaryRes, topRes, fieldRes] = await Promise.all([
        api.get('/wells'),
        api.get('/wells/summary'),
        api.get('/analytics/top-producers'),
        api.get('/analytics/field-comparison'),
      ]);
      setWells(wellsRes.data);
      setSummary(summaryRes.data);
      setTopProducers(topRes.data);
      setFieldComparison(fieldRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load dashboard data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadDashboard();
    }, [loadDashboard])
  );

  const totalOil = summary.reduce((sum, well) => sum + Number(well.total_oil_bbl || 0), 0);
  const activeWells = wells.filter((well) => well.status === 'active').length;

  const topChartData = {
    labels: topProducers.map((well) => well.well_name).slice(0, 5),
    datasets: [{ data: topProducers.map((well) => Math.round(well.total_oil_bbl || 0)).slice(0, 5) }],
  };

  const fieldChartData = {
    labels: fieldComparison.map((field) => field.field_name),
    datasets: [{ data: fieldComparison.map((field) => Math.round(field.total_oil_bbl || 0)) }],
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.orange} size="large" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => {
        setRefreshing(true);
        loadDashboard();
      }} tintColor={colors.orange} />}
    >
      <Text style={styles.screenTitle}>Field Operations Overview</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.statsGrid}>
        <StatCard label="Total Wells" value={wells.length} icon="water" />
        <StatCard label="Active Wells" value={activeWells} icon="pulse" />
        <StatCard label="Total Oil bbl" value={Math.round(totalOil).toLocaleString()} icon="flame" />
      </View>

      <Section title="Top 5 Producers">
        {topProducers.length ? (
          <BarChart
            data={topChartData}
            width={chartWidth}
            height={260}
            yAxisLabel=""
            yAxisSuffix=""
            chartConfig={chartConfig}
            style={styles.chart}
            fromZero
            showValuesOnTopOfBars
          />
        ) : (
          <EmptyChart message="No producer data available." />
        )}
      </Section>

      <Section title="Field Comparison">
        {fieldComparison.length ? (
          <BarChart
            data={fieldChartData}
            width={chartWidth}
            height={260}
            yAxisLabel=""
            yAxisSuffix=""
            chartConfig={chartConfig}
            style={styles.chart}
            fromZero
            showValuesOnTopOfBars
          />
        ) : (
          <EmptyChart message="No field comparison data available." />
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
  statsGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    minHeight: 112,
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    justifyContent: 'space-between',
  },
  statValue: {
    color: colors.white,
    fontSize: 20,
    fontWeight: '800',
  },
  statLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
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
  emptyChart: {
    height: 180,
    backgroundColor: colors.card,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
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
