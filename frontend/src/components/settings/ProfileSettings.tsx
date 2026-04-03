import React, { useState, useEffect } from 'react';
import { ShieldCheck, Mail, Building2, Clock, Save, Check, X } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Label } from '../../components/ui/Label';
import { Badge } from '../../components/ui/Badge';
import { useAuthStore } from '../../stores/authStore';
import { useToast } from '../../context/ToastContext';

interface ProfileData {
  business_name: string;
  business_description: string;
  bot_name: string;
  business_hours: {
    monday: string;
    tuesday: string;
    wednesday: string;
    thursday: string;
    friday: string;
    saturday: string;
    sunday: string;
  };
}

export const ProfileSettings: React.FC = () => {
  const { merchant } = useAuthStore();
  const { toast } = useToast();

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [profileData, setProfileData] = useState<ProfileData>({
    business_name: '',
    business_description: '',
    bot_name: '',
    business_hours: {
      monday: '',
      tuesday: '',
      wednesday: '',
      thursday: '',
      friday: '',
      saturday: '',
      sunday: '',
    },
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Load profile data on mount
  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/v1/merchant/profile', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to load profile');
        }

        const envelope = await response.json();
        const data = envelope.data;

        setProfileData({
          business_name: data.business_name || '',
          business_description: data.business_description || '',
          bot_name: data.bot_name || '',
          business_hours: data.business_hours || {
            monday: '',
            tuesday: '',
            wednesday: '',
            thursday: '',
            friday: '',
            saturday: '',
            sunday: '',
          },
        });
      } catch (error) {
        toast('Failed to load profile data', 'error');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleChange = (field: keyof ProfileData, value: string) => {
    setProfileData((prev) => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
    setSaveStatus('idle');
  };

  const handleBusinessHoursChange = (day: string, value: string) => {
    setProfileData((prev) => ({
      ...prev,
      business_hours: {
        ...prev.business_hours,
        [day]: value,
      },
    }));
    setHasChanges(true);
    setSaveStatus('idle');
  };

  const handleSave = async () => {
    if (!hasChanges) {
      toast('No changes to save', 'error');
      return;
    }

    setIsSaving(true);
    setSaveStatus('idle');

    try {
      const response = await fetch('/api/v1/merchant/profile', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          business_name: profileData.business_name || undefined,
          business_description: profileData.business_description || undefined,
          bot_name: profileData.bot_name || undefined,
          business_hours: profileData.business_hours,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update profile');
      }

      const envelope = await response.json();
      const updatedData = envelope.data;

      setProfileData({
        business_name: updatedData.business_name || '',
        business_description: updatedData.business_description || '',
        bot_name: updatedData.bot_name || '',
        business_hours: updatedData.business_hours || profileData.business_hours,
      });

      setHasChanges(false);
      setSaveStatus('success');
      toast('Profile updated successfully', 'success');

      // Reset save status after 3 seconds
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      console.error(error);
      setSaveStatus('error');
      toast('Failed to update profile', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="glass-panel rounded-2xl p-10 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-container"></div>
        <p className="ml-4 text-on-surface-variant">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-headline text-xl font-bold text-[#d7fff3] mb-1">Profile Information</h3>
          <p className="text-sm text-on-surface-variant">
            Manage your business information and bot settings
          </p>
        </div>

        {saveStatus === 'success' && (
          <Badge variant="success" className="animate-in fade-in">
            ✓ Saved
          </Badge>
        )}
      </div>

      {/* Basic Information */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h4 className="font-semibold text-[#d7fff3] flex items-center gap-2">
          <Building2 size={18} className="text-primary-container" />
          Business Information
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="business_name" className="text-white font-medium">Business Name</Label>
            <Input
              id="business_name"
              value={profileData.business_name}
              onChange={(e) => handleChange('business_name', e.target.value)}
              placeholder="Your Business Name"
              className="bg-surface-container border-outline-variant text-white placeholder:text-white/50"
            />
          </div>

          <div>
            <Label htmlFor="bot_name" className="text-white font-medium">Bot Name</Label>
            <Input
              id="bot_name"
              value={profileData.bot_name}
              onChange={(e) => handleChange('bot_name', e.target.value)}
              placeholder="Bot Display Name"
              className="bg-surface-container border-outline-variant text-white placeholder:text-white/50"
            />
          </div>
        </div>

        <div>
          <Label htmlFor="business_description" className="text-white font-medium">Business Description</Label>
          <textarea
            id="business_description"
            value={profileData.business_description}
            onChange={(e) => handleChange('business_description', e.target.value)}
            placeholder="Describe your business..."
            rows={3}
            className="w-full bg-surface-container border border-outline-variant rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/50 focus:outline-none focus:ring-2 focus:ring-primary-container/30"
          />
        </div>
      </div>

      {/* Business Hours */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h4 className="font-semibold text-[#d7fff3] flex items-center gap-2">
          <Clock size={18} className="text-primary-container" />
          Business Hours
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
          ].map((day) => (
            <div key={day}>
              <Label htmlFor={day} className="capitalize text-white font-medium">{day}</Label>
              <Input
                id={day}
                value={profileData.business_hours[day as keyof typeof profileData.business_hours]}
                onChange={(e) => handleBusinessHoursChange(day, e.target.value)}
                placeholder="9:00 AM - 5:00 PM"
                className="bg-surface-container border-outline-variant text-white placeholder:text-white/50"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Account Email */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h4 className="font-semibold text-[#d7fff3] flex items-center gap-2">
          <Mail size={18} className="text-primary-container" />
          Account Email
        </h4>

        <div className="flex items-center justify-between p-3 bg-surface-container/50 rounded-lg border border-outline-variant">
          <div>
            <p className="text-sm font-medium text-on-surface">{merchant?.email || 'Not set'}</p>
            <p className="text-xs text-on-surface-variant">Primary email for account access</p>
          </div>
          <Button variant="outline" size="sm" disabled>
            Change Email
          </Button>
        </div>
      </div>

      {/* Account Status */}
      <div className="glass-panel p-6 rounded-xl space-y-4">
        <h4 className="font-semibold text-[#d7fff3] flex items-center gap-2">
          <ShieldCheck size={18} className="text-primary-container" />
          Account Status
        </h4>

        <div className="flex items-center gap-4 p-3 bg-surface-container/50 rounded-lg border border-outline-variant">
          <div className="w-2 h-2 rounded-full bg-primary-fixed"></div>
          <div>
            <p className="text-sm font-medium text-on-surface">Active</p>
            <p className="text-xs text-on-surface-variant">Enterprise Plan • All features enabled</p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      {hasChanges && (
        <div className="flex justify-end">
          <Button
            onClick={handleSave}
            disabled={isSaving || !hasChanges}
            className="bg-primary-container hover:bg-primary-fixed text-on-primary-container font-semibold"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-on-primary-container mr-2"></div>
                Saving...
              </>
            ) : (
              <>
                <Save size={18} className="mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};
