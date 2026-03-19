export interface BusinessHoursConfig {
  timezone?: string;
  hours?: Record<string, { open: string; close: string } | null>;
}

export function getBusinessHoursMessage(businessHours: BusinessHoursConfig | null): string {
  if (!businessHours?.hours) return 'Contact us';
  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const now = new Date();
  const today = days[now.getDay()];
  const todayHours = businessHours.hours[today];
  if (!todayHours) return 'Contact us';
  const currentTime = now.getHours() * 60 + now.getMinutes();
  const [openH, openM] = todayHours.open.split(':').map(Number);
  const [closeH, closeM] = todayHours.close.split(':').map(Number);
  if (currentTime >= openH * 60 + openM && currentTime < closeH * 60 + closeM) {
    return 'Available now';
  }
  for (let i = 1; i <= 7; i++) {
    const nextDay = days[(now.getDay() + i) % 7];
    const nextHours = businessHours.hours[nextDay];
    if (nextHours) {
      return `Available ${nextDay} at ${nextHours.open}`;
    }
  }
  return 'Contact us';
}
