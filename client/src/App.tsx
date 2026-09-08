type Status = "NEW" | "IN_PROGRESS" | "COMPLETED";
type Priority = "LOW" | "MEDIUM" | "HIGH";


type Task = {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  status: Status;
  createdAt: string;
}


type Analysis = {
  category: string;
  priority: Priority;
  summary: string;
  recommendedAction: string;
}

const statuses: Array<Status | "ALL"> = [ // all is for the filter option for showing all the statuses
  "ALL",
  "NEW",
  "IN_PROGRESS",
  "COMPLETED"
];
