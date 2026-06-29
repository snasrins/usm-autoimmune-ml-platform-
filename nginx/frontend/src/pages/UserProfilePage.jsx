import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import {
  User,
  Mail,
  Shield,
  Calendar,
  Activity,
  Award,
  Clock,
  Database,
  Brain,
  TrendingUp,
  ChevronLeft,
  Edit,
  Save,
  X
} from 'lucide-react';

export default function UserProfilePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedUser, setEditedUser] = useState({});

  // Mock activity data
  const [activityStats, setActivityStats] = useState({
    datasetsUploaded: 12,
    modelsCreated: 8,
    experimentsRun: 47,
    gpuHoursUsed: 23.5,
    lastLogin: '2026-04-05 09:15:22',
    accountCreated: '2025-09-12'
  });

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      setEditedUser(userData);
    } catch (error) {
      console.error('Failed to load user data:', error);
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      // API call to update user profile would go here
      setUser(editedUser);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-[#7B5CF0] border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-[#8585A0]">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #EBEBEE 0%, #E8E5F5 50%, #F0EDF8 100%)' }}>
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-[#8585A0] hover:text-[#7B5CF0] transition-colors mb-4"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="text-[12px] font-medium">Back to Dashboard</span>
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-syne text-[28px] font-bold text-[#0F0F11]">User Profile</h1>
              <p className="text-[13px] text-[#8585A0] mt-1">Manage your account settings and view activity</p>
            </div>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center gap-2 px-4 py-2 bg-[#0F0F11] hover:bg-[#0F0F11]/90 text-white rounded-xl transition-all hover:-translate-y-0.5 shadow-sm"
              >
                <Edit className="w-4 h-4" />
                <span className="text-[12px] font-medium">Edit Profile</span>
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditedUser(user);
                    setIsEditing(false);
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-[#0F0F11] rounded-xl transition-colors hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                  <span className="text-[12px] font-medium">Cancel</span>
                </button>
                <button
                  onClick={handleSave}
                  className="flex items-center gap-2 px-4 py-2 bg-[#7B5CF0] hover:bg-[#7B5CF0]/90 text-white rounded-xl transition-all hover:-translate-y-0.5 shadow-sm"
                >
                  <Save className="w-4 h-4" />
                  <span className="text-[12px] font-medium">Save Changes</span>
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Left: Profile Card */}
          <div className="col-span-1 space-y-4">
            <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md p-6">
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-[rgba(123,92,240,0.12)] border-2 border-[#7B5CF0]/30 flex items-center justify-center mb-4">
                  <span className="font-syne text-[32px] font-bold text-[#7B5CF0]">
                    {user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'U'}
                  </span>
                </div>
                
                {isEditing ? (
                  <input
                    type="text"
                    value={editedUser.full_name || ''}
                    onChange={(e) => setEditedUser({...editedUser, full_name: e.target.value})}
                    className="w-full text-center font-syne text-[18px] font-bold text-[#0F0F11] mb-1 px-3 py-2 bg-white border border-gray-200 rounded-lg focus:outline-none focus:border-[#7B5CF0] focus:ring-3 focus:ring-[rgba(123,92,240,0.12)]"
                  />
                ) : (
                  <h2 className="font-syne text-[18px] font-bold text-[#0F0F11] mb-1">{user?.full_name}</h2>
                )}
                
                <div className="flex items-center gap-2 mb-4">
                  <Shield className="w-3.5 h-3.5 text-[#7B5CF0]" />
                  <span className="text-[12px] text-[#8585A0] font-medium">{user?.role}</span>
                </div>

                <div className="w-full space-y-3 pt-4 border-t border-gray-200">
                  <ProfileField icon={Mail} label="Email" value={user?.email} isEditing={isEditing} editedValue={editedUser.email} onChange={(v) => setEditedUser({...editedUser, email: v})} />
                  <ProfileField icon={User} label="Username" value={user?.username} />
                  <ProfileField icon={Calendar} label="Joined" value={activityStats.accountCreated} />
                  <ProfileField icon={Clock} label="Last Login" value={activityStats.lastLogin} />
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-[#F5F5F7] rounded-2xl border border-gray-200 shadow-sm p-4">
              <h3 className="font-syne text-[13px] font-bold text-[#0F0F11] mb-3">Quick Stats</h3>
              <div className="space-y-2">
                <QuickStat icon={Database} label="Datasets" value={activityStats.datasetsUploaded} />
                <QuickStat icon={Brain} label="Models" value={activityStats.modelsCreated} />
                <QuickStat icon={Activity} label="Experiments" value={activityStats.experimentsRun} />
                <QuickStat icon={TrendingUp} label="GPU Hours" value={`${activityStats.gpuHoursUsed}h`} />
              </div>
            </div>
          </div>

          {/* Right: Activity & Settings */}
          <div className="col-span-2 space-y-4">
            {/* Recent Activity */}
            <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-syne text-[15px] font-bold text-[#0F0F11]">Recent Activity</h3>
              </div>
              <div className="p-6 space-y-3">
                <ActivityItem
                  icon={Database}
                  action="Uploaded dataset"
                  detail="HUSM_batch3.csv (4,284 records)"
                  time="2 hours ago"
                  color="text-[#7B5CF0]"
                />
                <ActivityItem
                  icon={Brain}
                  action="Created model"
                  detail="SLE_classifier_v2.1 (RandomForest)"
                  time="5 hours ago"
                  color="text-[#10B981]"
                />
                <ActivityItem
                  icon={Activity}
                  action="Ran experiment"
                  detail="Hyperparameter tuning - 24 trials"
                  time="1 day ago"
                  color="text-[#F59E0B]"
                />
                <ActivityItem
                  icon={TrendingUp}
                  action="Model deployed"
                  detail="disease_activity_v1 → staging"
                  time="2 days ago"
                  color="text-[#3B82F6]"
                />
                <ActivityItem
                  icon={Database}
                  action="Validated data quality"
                  detail="combined_v2 (98.2% score)"
                  time="3 days ago"
                  color="text-[#10B981]"
                />
              </div>
            </div>

            {/* Preferences */}
            <div className="bg-[#F5F5F7] rounded-[28px] border border-gray-200 shadow-md">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-syne text-[15px] font-bold text-[#0F0F11]">Preferences</h3>
              </div>
              <div className="p-6 space-y-4">
                <PreferenceSetting
                  label="Email Notifications"
                  description="Receive updates on model training and data quality"
                  enabled={true}
                />
                <PreferenceSetting
                  label="GPU Quota Alerts"
                  description="Get notified when GPU usage exceeds 80%"
                  enabled={true}
                />
                <PreferenceSetting
                  label="Weekly Summary"
                  description="Email digest of platform activity"
                  enabled={false}
                />
              </div>
            </div>

            {/* Achievements */}
            <div className="bg-[#F5F5F7] rounded-2xl border border-gray-200 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-syne text-[13px] font-bold text-[#0F0F11]">Achievements</h3>
              </div>
              <div className="p-6 grid grid-cols-3 gap-3">
                <AchievementBadge icon={Award} label="First Model" earned />
                <AchievementBadge icon={Database} label="10 Datasets" earned />
                <AchievementBadge icon={Activity} label="50 Experiments" locked />
                <AchievementBadge icon={TrendingUp} label="Production Deploy" earned />
                <AchievementBadge icon={Brain} label="ML Expert" locked />
                <AchievementBadge icon={Shield} label="Data Guardian" locked />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Components
function ProfileField({ icon: Icon, label, value, isEditing, editedValue, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <Icon className="w-4 h-4 text-[#8585A0]" />
      <div className="flex-1">
        <div className="text-[10px] text-[#8585A0] uppercase tracking-wide mb-0.5">{label}</div>
        {isEditing && onChange ? (
          <input
            type="text"
            value={editedValue || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full text-[12px] text-[#0F0F11] font-medium px-2 py-1 bg-white border border-gray-200 rounded focus:outline-none focus:border-[#7B5CF0]"
          />
        ) : (
          <div className="text-[12px] text-[#0F0F11] font-medium">{value}</div>
        )}
      </div>
    </div>
  );
}

function QuickStat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-[#7B5CF0]" />
        <span className="text-[11px] text-[#8585A0]">{label}</span>
      </div>
      <span className="text-[12px] text-[#0F0F11] font-bold">{value}</span>
    </div>
  );
}

function ActivityItem({ icon: Icon, action, detail, time, color }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-white/50 transition-colors">
      <div className={`w-8 h-8 rounded-lg bg-white flex items-center justify-center ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12px] text-[#0F0F11] font-medium">{action}</div>
        <div className="text-[11px] text-[#8585A0] truncate">{detail}</div>
      </div>
      <span className="text-[10px] text-[#8585A0] flex-shrink-0">{time}</span>
    </div>
  );
}

function PreferenceSetting({ label, description, enabled }) {
  return (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="text-[12px] text-[#0F0F11] font-medium mb-0.5">{label}</div>
        <div className="text-[11px] text-[#8585A0]">{description}</div>
      </div>
      <button
        className={`relative w-11 h-6 rounded-full transition-colors ${
          enabled ? 'bg-[#7B5CF0]' : 'bg-gray-300'
        }`}
      >
        <div
          className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
            enabled ? 'translate-x-5' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  );
}

function AchievementBadge({ icon: Icon, label, earned, locked }) {
  return (
    <div
      className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all ${
        earned
          ? 'bg-[rgba(123,92,240,0.12)] border-[#7B5CF0]/30'
          : 'bg-white border-gray-200 opacity-50'
      }`}
    >
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center ${
          earned ? 'bg-[#7B5CF0]' : 'bg-gray-300'
        }`}
      >
        <Icon className="w-5 h-5 text-white" />
      </div>
      <span className="text-[10px] text-[#0F0F11] font-medium text-center">{label}</span>
      {locked && <div className="text-[8px] text-[#8585A0]">Locked</div>}
    </div>
  );
}
