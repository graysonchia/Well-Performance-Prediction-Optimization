import 'react-native-gesture-handler';
import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import AnalyticsScreen from './screens/AnalyticsScreen';
import DashboardScreen from './screens/DashboardScreen';
import LoginScreen from './screens/LoginScreen';
import WellDetailScreen from './screens/WellDetailScreen';
import WellsScreen from './screens/WellsScreen';
import { colors } from './constants/theme';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function WellsStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.navy },
        headerTintColor: colors.white,
        headerTitleStyle: { fontWeight: '700' },
        cardStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="WellsList" component={WellsScreen} options={{ title: 'Wells' }} />
      <Stack.Screen name="WellDetail" component={WellDetailScreen} options={{ title: 'Well Detail' }} />
    </Stack.Navigator>
  );
}

function AppTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerStyle: { backgroundColor: colors.navy },
        headerTintColor: colors.white,
        tabBarStyle: { backgroundColor: colors.navy, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.orange,
        tabBarInactiveTintColor: colors.muted,
        tabBarIcon: ({ color, size }) => {
          const icons = {
            Dashboard: 'speedometer',
            Wells: 'water',
            Analytics: 'analytics',
          };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Wells" component={WellsStack} options={{ headerShown: false }} />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    async function loadToken() {
      const token = await AsyncStorage.getItem('token');
      setIsAuthenticated(Boolean(token));
      setIsLoading(false);
    }

    loadToken();
  }, []);

  const navigationTheme = useMemo(
    () => ({
      ...DefaultTheme,
      colors: {
        ...DefaultTheme.colors,
        background: colors.background,
        card: colors.navy,
        text: colors.white,
        border: colors.border,
        primary: colors.orange,
      },
    }),
    []
  );

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.orange} size="large" />
        <Text style={styles.loadingText}>Loading Well Analytics...</Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer theme={navigationTheme}>
        {isAuthenticated ? (
          <AppTabs />
        ) : (
          <LoginScreen onLogin={() => setIsAuthenticated(true)} />
        )}
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    marginTop: 12,
    color: colors.white,
    fontWeight: '700',
  },
});
