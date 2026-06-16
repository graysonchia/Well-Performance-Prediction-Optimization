import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

import { colors, spacing } from '../constants/theme';
import api from '../services/api';

const statusColors = {
  active: colors.green,
  inactive: colors.red,
  maintenance: colors.yellow,
  abandoned: colors.muted,
};

function WellCard({ well, onPress }) {
  const badgeColor = statusColors[well.status] || colors.muted;

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}>
      <View style={styles.cardHeader}>
        <View style={styles.titleBlock}>
          <Text style={styles.wellName}>{well.well_name}</Text>
          <Text style={styles.fieldName}>{well.field_name}</Text>
        </View>
        <View style={[styles.badge, { borderColor: badgeColor }]}>
          <View style={[styles.badgeDot, { backgroundColor: badgeColor }]} />
          <Text style={styles.badgeText}>{well.status}</Text>
        </View>
      </View>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <Ionicons name="construct" size={15} color={colors.orange} />
          <Text style={styles.metaText}>{well.well_type}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="resize" size={15} color={colors.orange} />
          <Text style={styles.metaText}>{Math.round(well.depth_m || 0).toLocaleString()} m</Text>
        </View>
      </View>
    </Pressable>
  );
}

export default function WellsScreen({ navigation }) {
  const [wells, setWells] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const loadWells = useCallback(async () => {
    setError('');
    try {
      const response = await api.get('/wells');
      setWells(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load wells.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadWells();
    }, [loadWells])
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.orange} size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <FlatList
        data={wells}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => {
          setRefreshing(true);
          loadWells();
        }} tintColor={colors.orange} />}
        renderItem={({ item }) => (
          <WellCard
            well={item}
            onPress={() => navigation.navigate('WellDetail', { wellId: item.id, wellName: item.well_name })}
          />
        )}
        ListEmptyComponent={<Text style={styles.empty}>No wells found.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  list: {
    padding: spacing.screen,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 8,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardPressed: {
    opacity: 0.75,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  titleBlock: {
    flex: 1,
  },
  wellName: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '800',
  },
  fieldName: {
    color: colors.muted,
    marginTop: 4,
  },
  badge: {
    height: 28,
    paddingHorizontal: 10,
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgeDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  badgeText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'capitalize',
  },
  metaRow: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 14,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    color: colors.white,
    fontWeight: '700',
  },
  error: {
    color: colors.red,
    padding: spacing.screen,
    fontWeight: '700',
  },
  empty: {
    color: colors.muted,
    textAlign: 'center',
    marginTop: 40,
  },
});
