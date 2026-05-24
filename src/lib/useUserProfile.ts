import { getDemoProfiles, getEmployeeProfile, type EmployeeProfile } from "../services/employeeExperienceService";

export interface UserProfile extends EmployeeProfile {}

export const DEMO_PROFILES = getDemoProfiles();
export const MOCK_USER = {
  uid: DEMO_PROFILES[0].uid,
  email: DEMO_PROFILES[0].email,
  displayName: DEMO_PROFILES[0].displayName,
  photoURL: DEMO_PROFILES[0].photoURL ?? null,
} as const;

export function useUserProfile(userOrUid: any) {
  const uid = typeof userOrUid === "string"
    ? userOrUid
    : (userOrUid?.uid || DEMO_PROFILES[0].uid);

  const profile = getEmployeeProfile(uid);

  return {
    profile,
    loading: false,
    availableProfiles: DEMO_PROFILES,
  };
}
