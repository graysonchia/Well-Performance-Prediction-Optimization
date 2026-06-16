import React, { useCallback, useLayoutEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
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

function InfoItem({ icon, label, value }) {
  return (
    <View style={styles.infoItem}>
      <Ionicons name={icon} size={16} color={colors.orange} />
      <View style={styles.infoTextBlock}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
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

export default function WellDetailScreen({ route, navigation }) {
  const { wellId, wellName } = route.params;
  const [well, setWell] = useState(null);
  const [production, setProduction] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    navigation.setOptions({ title: wellName || 'Well Detail' });
  }, [navigation, wellName]);

  const loadDetail = useCallback(async () => {
    setError('');
    try {
      const [wellRes, productionRes, sensorsRes, maintenanceRes] = await Promise.all([
        api.get(`/wells/${wellId}`),
        api.get(`/wells/${wellId}/production`),
        api.get(`/wells/${wellId}/sensors`),
        api.get(`/wells/${wellId}/maintenance`),
      ]);
      setWell(wellRes.data);
      setProduction(productionRes.data);
      setSensors(sensorsRes.data);
      setMaintenance(maintenanceRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load well detail.');
    } finally {
      setLoading(false);
    }
  }, [wellId]);

  useFocusEffect(
    useCallback(() => {
      loadDetail();
    }, [loadDetail])
  );

  const last90 = useMemo(() => production.slice(-90), [production]);
  const latestSensor = sensors[sensors.length - 1];

  const oilPoints = downsample(last90);
  const oilChartData = {
    labels: oilPoints.map((item) => new Date(item.log_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
    datasets: [{ data: oilPoints.map((item) => Number(item.oil_bbl || 0)) }],
  };

  const waterPoints = downsample(
    last90.map((item) => ({
      ...item,
      water_cut_pct:
        Number(item.oil_bbl || 0) + Number(item.water_bbl || 0) > 0
          ? (Number(item.water_bbl || 0) / (Number(item.oil_bbl || 0) + Number(item.water_bbl || 0))) * 100
          : 0,
    }))
  );
  const waterChartData = {
    labels: waterPoints.map((item) => new Date(item.log_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
    datasets: [{ data: waterPoints.map((item) => Number(item.water_cut_pct || 0)) }],
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.orange} size="large" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {well ? (
        <View style={styles.header}>
          <Text style={styles.wellName}>{well.well_name}</Text>
          <Text style={styles.fieldName}>{well.field_name}</Text>
          <View style={styles.infoGrid}>
            <InfoItem icon="business" label="Operator" value={well.operator} />
            <InfoItem icon="resize" label="Depth" value={`${Math.round(well.depth_m || 0).toLocaleString()} m`} />
            <InfoItem icon="navigate" label="Latitude" value={Number(well.latitude).toFixed(4)} />
            <InfoItem icon="map" label="Longitude" value={Number(well.longitude).toFixed(4)} />
          </View>
        </View>
      ) : null}

      <Section title="Production Trend - Last 90 Days">
        {oilPoints.length ? (
          <LineChart
            data={oilChartData}
            width={chartWidth}
            height={240}
            chartConfig={chartConfig}
            style={styles.chart}
            bezier
            fromZero
          />
        ) : (
          <EmptyState message="No production logs available." />
        )}
      </Section>

      <Section title="Water Cut Trend">
        {waterPoints.length ? (
          <LineChart
            data={waterChartData}
            width={chartWidth}
            height={240}
            chartConfig={chartConfig}
            style={styles.chart}
            bezier
            fromZero
            yAxisSuffix="%"
          />
        ) : (
          <EmptyState message="No water cut data available." />
        )}
      </Section>

      <Section title="Latest Sensor Summary">
        {latestSensor ? (
          <View style={styles.sensorGrid}>
            <InfoItem icon="thermometer" label="Temperature" value={`${Number(latestSensor.temperature_c || 0).toFixed(1)} C`} />
            <InfoItem icon="speedometer" label="Pressure" value={`${Math.round(latestSensor.pressure_psi || 0).toLocaleString()} psi`} />
            <InfoItem icon="trending-up" label="Flow Rate" value={`${Math.round(latestSensor.flow_rate_bpd || 0).toLocaleString()} bpd`} />
            <InfoItem icon="pulse" label="Vibration" value={`${Number(latestSensor.vibration_mms || 0).toFixed(2)} mm/s`} />
          </View>
        ) : (
          <EmptyState message="No sensor readings available." />
        )}
      </Section>

      <Section title="Recent Maintenance">
        {maintenance.slice(-5).reverse().map((event) => (
          <View key={event.id} style={styles.eventRow}>
            <View style={styles.eventIcon}>
              <Ionicons name={event.is_unplanned ? 'warning' : 'construct'} size={18} color={colors.orange} />
            </View>
            <View style={styles.eventBody}>
              <Text style={styles.eventTitle}>{event.event_type}</Text>
              <Text style={styles.eventMeta}>
                {new Date(event.event_date).toLocaleDateString()} · {event.duration_hrs} hrs · ${Math.round(event.cost_usd || 0).toLocaleString()}
              </Text>
            </View>
          </View>
        ))}
        {!maintenance.length ? <EmptyState message="No maintenance events available." /> : null}
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
  header: {
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 18,
  },
  wellName: {
    color: colors.white,
    fontSize: 25,
    fontWeight: '800',
  },
  fieldName: {
    color: colors.orange,
    fontWeight: '800',
    marginTop: 4,
  },
  infoGrid: {
    marginTop: 14,
    gap: 10,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  infoTextBlock: {
    flex: 1,
  },
  infoLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
  },
  infoValue: {
    color: colors.white,
    fontWeight: '800',
    marginTop: 2,
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
  sensorGrid: {
    backgroundColor: colors.card,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    gap: 12,
  },
  eventRow: {
    flexDirection: 'row',
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  eventIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.navy,
  },
  eventBody: {
    flex: 1,
  },
  eventTitle: {
    color: colors.white,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  eventMeta: {
    color: colors.muted,
    marginTop: 4,
    fontSize: 12,
  },
  emptyState: {
    minHeight: 120,
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
