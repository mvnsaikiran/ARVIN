import { getEmployeeRecord } from "./employeeExperienceService";

export function getEmployeeData(userId: string) {
  return getEmployeeRecord(userId);
}

export const hrisTools = {
  get_leave_balance: ({ userId }: { userId: string }) => {
    const data = getEmployeeRecord(userId);
    return { balance: data.leaveBalances };
  },
  get_latest_pay_stub: ({ userId }: { userId: string }) => {
    const data = getEmployeeRecord(userId);
    return { latestStub: data.payStubs[0] };
  },
  get_benefits_status: ({ userId }: { userId: string }) => {
    const data = getEmployeeRecord(userId);
    return { status: data.benefits.enrollmentStatus, plan: data.benefits.health, retirement: data.benefits.retirement };
  },
};

export const toolDefinitions = [
  {
    name: "get_leave_balance",
    description: "Retrieves the current remaining leave balance for the authenticated employee.",
    parameters: {
      type: "OBJECT",
      properties: {
        userId: { type: "STRING", description: "The unique identifier of the employee." },
      },
      required: ["userId"],
    },
  },
  {
    name: "get_latest_pay_stub",
    description: "Retrieves the most recent pay stub information including gross and net pay.",
    parameters: {
      type: "OBJECT",
      properties: {
        userId: { type: "STRING" },
      },
      required: ["userId"],
    },
  },
  {
    name: "get_benefits_status",
    description: "Checks current benefit enrollment status and active plan details.",
    parameters: {
      type: "OBJECT",
      properties: {
        userId: { type: "STRING" },
      },
      required: ["userId"],
    },
  },
];
