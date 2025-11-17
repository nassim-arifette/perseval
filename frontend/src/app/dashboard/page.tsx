'use client';

import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, theme, animations } from '../lib/theme';
import { Card } from '../components/ui/Card';
import { storage } from '../lib/storage';
import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar } from 'recharts';

export default function DashboardPage() {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);
  const [stats, setStats] = useState({
    total: 0,
    scam: 0,
    safe: 0,
    uncertain: 0,
    scamPercentage: 0,
  });
  const [recentAnalyses, setRecentAnalyses] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    // Load data from storage
    const storageStats = storage.getStats();
    setStats(storageStats);

    const recent = storage.getRecent(10);
    setRecentAnalyses(recent);

    // Prepare chart data
    const pieData = [
      { name: 'Scam', value: storageStats.scam, color: colors.accent.danger },
      { name: 'Safe', value: storageStats.safe, color: colors.accent.success },
      { name: 'Uncertain', value: storageStats.uncertain, color: colors.accent.warning },
    ];
    setChartData(pieData);
  }, []);

  const StatCard = ({ title, value, icon, gradient }: any) => (
    <Card hover padding="lg" gradient={gradient}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
            {title}
          </p>
          <motion.p
            className="text-4xl font-bold"
            style={{ color: colors.text.primary }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15 }}
          >
            {value}
          </motion.p>
        </div>
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-2xl"
          style={{ background: gradient || theme.gradients.primary }}
        >
          {icon}
        </div>
      </div>
    </Card>
  );

  return (
    <div
      className="min-h-screen p-8"
      style={{ backgroundColor: colors.background.secondary }}
    >
      <motion.div
        initial="initial"
        animate="animate"
        variants={animations.staggerContainer}
        className="max-w-7xl mx-auto"
      >
        {/* Header */}
        <motion.div variants={animations.slideUp} className="mb-8">
          <h1
            className="text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent"
          >
            Dashboard
          </h1>
          <p style={{ color: colors.text.secondary }}>
            Overview of your scam detection activity
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={animations.staggerContainer}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <motion.div variants={animations.staggerItem}>
            <StatCard
              title="Total Checks"
              value={stats.total}
              gradient={theme.gradients.primary}
              icon="📊"
            />
          </motion.div>
          <motion.div variants={animations.staggerItem}>
            <StatCard
              title="Scams Detected"
              value={stats.scam}
              gradient={theme.gradients.danger}
              icon="⚠️"
            />
          </motion.div>
          <motion.div variants={animations.staggerItem}>
            <StatCard
              title="Safe Messages"
              value={stats.safe}
              gradient={theme.gradients.success}
              icon="✅"
            />
          </motion.div>
          <motion.div variants={animations.staggerItem}>
            <StatCard
              title="Uncertain"
              value={stats.uncertain}
              gradient={theme.gradients.warning}
              icon="❓"
            />
          </motion.div>
        </motion.div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Pie Chart */}
          <motion.div variants={animations.slideUp}>
            <Card padding="lg">
              <h3
                className="text-xl font-bold mb-6"
                style={{ color: colors.text.primary }}
              >
                Detection Distribution
              </h3>
              {stats.total > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      animationBegin={0}
                      animationDuration={800}
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center">
                  <p style={{ color: colors.text.tertiary }}>
                    No data yet. Start checking messages!
                  </p>
                </div>
              )}
            </Card>
          </motion.div>

          {/* Risk Score Card */}
          <motion.div variants={animations.slideUp}>
            <Card padding="lg">
              <h3
                className="text-xl font-bold mb-6"
                style={{ color: colors.text.primary }}
              >
                Scam Detection Rate
              </h3>
              <div className="flex flex-col items-center justify-center h-[300px]">
                <motion.div
                  className="relative w-48 h-48"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 20 }}
                >
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="96"
                      cy="96"
                      r="80"
                      stroke={colors.border.default}
                      strokeWidth="12"
                      fill="none"
                    />
                    <motion.circle
                      cx="96"
                      cy="96"
                      r="80"
                      stroke={colors.accent.danger}
                      strokeWidth="12"
                      fill="none"
                      strokeLinecap="round"
                      initial={{ strokeDashoffset: 502 }}
                      animate={{
                        strokeDashoffset: 502 - (502 * stats.scamPercentage) / 100,
                      }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                      style={{
                        strokeDasharray: 502,
                      }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <motion.p
                      className="text-4xl font-bold"
                      style={{ color: colors.text.primary }}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.5 }}
                    >
                      {stats.scamPercentage.toFixed(1)}%
                    </motion.p>
                    <p className="text-sm" style={{ color: colors.text.tertiary }}>
                      Scam Rate
                    </p>
                  </div>
                </motion.div>
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Recent Activity */}
        <motion.div variants={animations.slideUp}>
          <Card padding="lg">
            <h3
              className="text-xl font-bold mb-6"
              style={{ color: colors.text.primary }}
            >
              Recent Activity
            </h3>
            {recentAnalyses.length > 0 ? (
              <div className="space-y-4">
                {recentAnalyses.map((analysis, index) => (
                  <motion.div
                    key={analysis.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-4 p-4 rounded-xl"
                    style={{
                      backgroundColor: colors.background.hover,
                      border: `1px solid ${colors.border.default}`,
                    }}
                  >
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                      style={{
                        backgroundColor:
                          analysis.result.message_prediction.label === 'scam'
                            ? colors.risk.high.bg
                            : analysis.result.message_prediction.label === 'not_scam'
                            ? colors.risk.low.bg
                            : colors.risk.medium.bg,
                      }}
                    >
                      {analysis.result.message_prediction.label === 'scam'
                        ? '⚠️'
                        : analysis.result.message_prediction.label === 'not_scam'
                        ? '✅'
                        : '❓'}
                    </div>
                    <div className="flex-1">
                      <p
                        className="font-medium line-clamp-1"
                        style={{ color: colors.text.primary }}
                      >
                        {analysis.input.text?.substring(0, 80)}...
                      </p>
                      <p className="text-sm" style={{ color: colors.text.tertiary }}>
                        {new Date(analysis.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div
                      className="px-3 py-1 rounded-full text-xs font-semibold capitalize"
                      style={{
                        backgroundColor:
                          analysis.result.message_prediction.label === 'scam'
                            ? colors.accent.danger
                            : analysis.result.message_prediction.label === 'not_scam'
                            ? colors.accent.success
                            : colors.accent.warning,
                        color: colors.text.inverse,
                      }}
                    >
                      {analysis.result.message_prediction.label.replace('_', ' ')}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p style={{ color: colors.text.tertiary }}>
                  No recent activity. Start checking messages to see them here!
                </p>
              </div>
            )}
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}
