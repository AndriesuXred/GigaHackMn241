// src/notification.ts
import * as Notifications from "expo-notifications";
import Constants from "expo-constants";
import { Platform } from "react-native";

// Notification handler (controls if banners/sounds show)

// Schedule a local notification
export async function schedulePushNotification() {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: "You've got mail! 📬",
      body: "Here is the notification body",
      data: { test: "data goes here" },
    },
    trigger: { seconds: 2 } as Notifications.TimeIntervalTriggerInput // 👈 simpler, no red error
  });
}

// Register and return Expo Push Token
export async function registerForPushNotificationsAsync() {
  let token;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("myNotificationChannel", {
      name: "Default Channel",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#FF231F7C",
    });
  }

  
  return token;
}
