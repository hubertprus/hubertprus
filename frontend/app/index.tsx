import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Platform,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';

const { width } = Dimensions.get('window');
const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || '';

interface Job {
  _id: string;
  title: string;
  description: string;
  job_type: string;
  word_count: number;
  price_gbp: number;
  status: string;
}

interface Stats {
  total_earnings_gbp: number;
  jobs_completed: number;
  jobs_available: number;
  today_earnings: number;
  this_week_earnings: number;
}

interface CompletedWork {
  _id: string;
  job_title: string;
  earnings_gbp: number;
  completed_at: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'history' | 'settings'>('dashboard');
  const [stats, setStats] = useState<Stats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [completedWorks, setCompletedWorks] = useState<CompletedWork[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [executingJob, setExecutingJob] = useState<string | null>(null);
  const [autoMode, setAutoMode] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchStats(),
        fetchJobs(),
        fetchCompletedWorks(),
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/jobs/available`);
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchCompletedWorks = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/work/history`);
      const data = await response.json();
      setCompletedWorks(data);
    } catch (error) {
      console.error('Error fetching completed works:', error);
    }
  };

  const executeJob = async (jobId: string) => {
    try {
      setExecutingJob(jobId);
      const response = await fetch(`${BACKEND_URL}/api/jobs/execute/${jobId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to execute job');
      }
      
      const result = await response.json();
      
      Alert.alert(
        'Success! 🎉',
        `Job completed! Earned £${result.earnings_gbp.toFixed(2)}`,
        [{ text: 'OK' }]
      );
      
      // Refresh data
      await loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to execute job. Please try again.');
      console.error('Error executing job:', error);
    } finally {
      setExecutingJob(null);
    }
  };

  const getJobTypeIcon = (type: string) => {
    switch (type) {
      case 'blog_post':
        return 'newspaper';
      case 'product_description':
        return 'pricetag';
      case 'social_media':
        return 'logo-instagram';
      case 'email_marketing':
        return 'mail';
      case 'article':
        return 'document-text';
      default:
        return 'create';
    }
  };

  const renderDashboard = () => (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>AI Money Maker</Text>
          <Text style={styles.headerSubtitle}>Zarabiaj przez AI</Text>
        </View>
        <TouchableOpacity
          style={[styles.autoModeButton, autoMode && styles.autoModeActive]}
          onPress={() => setAutoMode(!autoMode)}
        >
          <Ionicons
            name={autoMode ? 'flash' : 'flash-outline'}
            size={20}
            color="white"
          />
          <Text style={styles.autoModeText}>
            {autoMode ? 'AUTO ON' : 'AUTO OFF'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <View style={[styles.statsCard, styles.primaryCard]}>
          <Ionicons name="cash" size={32} color="#fff" />
          <Text style={styles.statsValue}>£{stats?.total_earnings_gbp.toFixed(2) || '0.00'}</Text>
          <Text style={styles.statsLabel}>Total Earnings</Text>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statsCardSmall}>
            <Ionicons name="today" size={24} color="#4CAF50" />
            <Text style={styles.statsValueSmall}>£{stats?.today_earnings.toFixed(2) || '0.00'}</Text>
            <Text style={styles.statsLabelSmall}>Today</Text>
          </View>

          <View style={styles.statsCardSmall}>
            <Ionicons name="calendar" size={24} color="#2196F3" />
            <Text style={styles.statsValueSmall}>£{stats?.this_week_earnings.toFixed(2) || '0.00'}</Text>
            <Text style={styles.statsLabelSmall}>This Week</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statsCardSmall}>
            <Ionicons name="checkmark-circle" size={24} color="#9C27B0" />
            <Text style={styles.statsValueSmall}>{stats?.jobs_completed || 0}</Text>
            <Text style={styles.statsLabelSmall}>Completed</Text>
          </View>

          <View style={styles.statsCardSmall}>
            <Ionicons name="list" size={24} color="#FF9800" />
            <Text style={styles.statsValueSmall}>{stats?.jobs_available || 0}</Text>
            <Text style={styles.statsLabelSmall}>Available</Text>
          </View>
        </View>
      </View>

      {/* Available Jobs */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Available Jobs</Text>
        {loading ? (
          <ActivityIndicator size="large" color="#6200EE" style={{ marginTop: 20 }} />
        ) : jobs.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="briefcase-outline" size={48} color="#ccc" />
            <Text style={styles.emptyStateText}>No jobs available</Text>
          </View>
        ) : (
          jobs.map((job) => (
            <View key={job._id} style={styles.jobCard}>
              <View style={styles.jobHeader}>
                <View style={styles.jobIconContainer}>
                  <Ionicons
                    name={getJobTypeIcon(job.job_type) as any}
                    size={24}
                    color="#6200EE"
                  />
                </View>
                <View style={styles.jobTitleContainer}>
                  <Text style={styles.jobTitle}>{job.title}</Text>
                  <Text style={styles.jobType}>{job.job_type.replace(/_/g, ' ')}</Text>
                </View>
              </View>

              <Text style={styles.jobDescription}>{job.description}</Text>

              <View style={styles.jobFooter}>
                <View style={styles.jobDetails}>
                  <Ionicons name="text" size={16} color="#666" />
                  <Text style={styles.jobDetailText}>{job.word_count} words</Text>
                </View>

                <View style={styles.jobPriceContainer}>
                  <Text style={styles.jobPrice}>£{job.price_gbp.toFixed(2)}</Text>
                </View>
              </View>

              <TouchableOpacity
                style={[
                  styles.executeButton,
                  executingJob === job._id && styles.executeButtonDisabled,
                ]}
                onPress={() => executeJob(job._id)}
                disabled={executingJob === job._id}
              >
                {executingJob === job._id ? (
                  <>
                    <ActivityIndicator size="small" color="#fff" />
                    <Text style={styles.executeButtonText}>Executing...</Text>
                  </>
                ) : (
                  <>
                    <Ionicons name="play-circle" size={20} color="#fff" />
                    <Text style={styles.executeButtonText}>Execute Job</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );

  const renderHistory = () => (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Work History</Text>
        <Text style={styles.headerSubtitle}>Completed Jobs</Text>
      </View>

      <View style={styles.section}>
        {loading ? (
          <ActivityIndicator size="large" color="#6200EE" style={{ marginTop: 20 }} />
        ) : completedWorks.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={48} color="#ccc" />
            <Text style={styles.emptyStateText}>No completed jobs yet</Text>
          </View>
        ) : (
          completedWorks.map((work) => (
            <View key={work._id} style={styles.historyCard}>
              <View style={styles.historyHeader}>
                <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
                <View style={styles.historyTitleContainer}>
                  <Text style={styles.historyTitle}>{work.job_title}</Text>
                  <Text style={styles.historyDate}>
                    {new Date(work.completed_at).toLocaleDateString('en-GB', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Text>
                </View>
              </View>
              <View style={styles.historyFooter}>
                <Text style={styles.historyEarnings}>£{work.earnings_gbp.toFixed(2)}</Text>
              </View>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );

  const renderSettings = () => (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
        <Text style={styles.headerSubtitle}>Configure your AI agent</Text>
      </View>

      <View style={styles.section}>
        <View style={styles.settingCard}>
          <View style={styles.settingHeader}>
            <Ionicons name="settings" size={24} color="#6200EE" />
            <Text style={styles.settingTitle}>AI Agent Status</Text>
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Auto Execute Mode</Text>
            <TouchableOpacity
              style={[styles.toggleButton, autoMode && styles.toggleButtonActive]}
              onPress={() => setAutoMode(!autoMode)}
            >
              <Text style={styles.toggleButtonText}>
                {autoMode ? 'ON' : 'OFF'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.settingCard}>
          <View style={styles.settingHeader}>
            <Ionicons name="information-circle" size={24} color="#2196F3" />
            <Text style={styles.settingTitle}>About</Text>
          </View>
          <Text style={styles.settingDescription}>
            This AI agent uses GPT-5.2 to automatically complete writing jobs and earn money in GBP.
          </Text>
          <Text style={styles.settingDescription}>
            Turn on Auto Mode to let the AI automatically pick up and complete available jobs.
          </Text>
        </View>

        <View style={styles.settingCard}>
          <View style={styles.settingHeader}>
            <Ionicons name="code" size={24} color="#4CAF50" />
            <Text style={styles.settingTitle}>AI Model</Text>
          </View>
          <Text style={styles.settingDescription}>OpenAI GPT-5.2</Text>
          <Text style={styles.settingDescription}>Emergent LLM Key Active</Text>
        </View>
      </View>
    </ScrollView>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Main Content */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'history' && renderHistory()}
      {activeTab === 'settings' && renderSettings()}

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <TouchableOpacity
          style={styles.navItem}
          onPress={() => setActiveTab('dashboard')}
        >
          <Ionicons
            name={activeTab === 'dashboard' ? 'home' : 'home-outline'}
            size={24}
            color={activeTab === 'dashboard' ? '#6200EE' : '#666'}
          />
          <Text
            style={[
              styles.navLabel,
              activeTab === 'dashboard' && styles.navLabelActive,
            ]}
          >
            Dashboard
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          onPress={() => setActiveTab('history')}
        >
          <Ionicons
            name={activeTab === 'history' ? 'time' : 'time-outline'}
            size={24}
            color={activeTab === 'history' ? '#6200EE' : '#666'}
          />
          <Text
            style={[
              styles.navLabel,
              activeTab === 'history' && styles.navLabelActive,
            ]}
          >
            History
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.navItem}
          onPress={() => setActiveTab('settings')}
        >
          <Ionicons
            name={activeTab === 'settings' ? 'settings' : 'settings-outline'}
            size={24}
            color={activeTab === 'settings' ? '#6200EE' : '#666'}
          />
          <Text
            style={[
              styles.navLabel,
              activeTab === 'settings' && styles.navLabelActive,
            ]}
          >
            Settings
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  autoModeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#666',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  autoModeActive: {
    backgroundColor: '#4CAF50',
  },
  autoModeText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 12,
  },
  statsContainer: {
    padding: 16,
  },
  primaryCard: {
    backgroundColor: '#6200EE',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statsCard: {
    backgroundColor: '#fff',
  },
  statsValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 8,
  },
  statsLabel: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  statsCardSmall: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  statsValueSmall: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statsLabelSmall: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  jobCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  jobHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  jobIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F3E5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  jobTitleContainer: {
    flex: 1,
  },
  jobTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  jobType: {
    fontSize: 12,
    color: '#666',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  jobDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  jobFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  jobDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  jobDetailText: {
    fontSize: 14,
    color: '#666',
  },
  jobPriceContainer: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  jobPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  executeButton: {
    backgroundColor: '#6200EE',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  executeButtonDisabled: {
    backgroundColor: '#9E9E9E',
  },
  executeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  historyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  historyHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  historyTitleContainer: {
    flex: 1,
    marginLeft: 12,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  historyDate: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  historyFooter: {
    alignItems: 'flex-end',
  },
  historyEarnings: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  settingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  settingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  settingTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  toggleButton: {
    backgroundColor: '#E0E0E0',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
  },
  toggleButtonActive: {
    backgroundColor: '#4CAF50',
  },
  toggleButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#999',
    marginTop: 12,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingBottom: Platform.OS === 'ios' ? 20 : 8,
    paddingTop: 8,
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
  },
  navLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  navLabelActive: {
    color: '#6200EE',
    fontWeight: '600',
  },
});
