import { useEffect, useState } from "react";

type Status = "NEW" | "IN_PROGRESS" | "COMPLETED";
type Priority = "LOW" | "MEDIUM" | "HIGH";
type Filter = Status | "ALL";

type Task = {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  status: Status;
  createdAt: string;
};

type Analysis = {
  category: string;
  priority: Priority;
  summary: string;
  recommendedAction: string;
};

const filters: Filter[] = [
  "ALL",
  "NEW",
  "IN_PROGRESS",
  "COMPLETED",
];

function formatStatus(status: Filter): string {
  return status === "ALL" ? "All statuses" : status.replace("_", " ");
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json();

  if (!response.ok) {
    throw new Error(body.detail ?? body.error ?? "Request failed.");
  }

  return body;
}

export function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [analysis, setAnalysis] = useState<Record<string, Analysis>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [analysingId, setAnalysingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadTasks() {
      setIsLoading(true);
      setError("");

      try {
        const query = filter === "ALL" ? "" : `?status=${filter}`;
        const result = await request<{ tasks: Task[] }>(`/tasks${query}`);

        if (active) {
          setTasks(result.tasks);
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load tasks.",
          );
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadTasks();

    return () => {
      active = false;
    };
  }, [filter]);

  async function updateStatus(id: string, status: Status) {
    setError("");

    try {
      const result = await request<{ task: Task }>(
        `/tasks/${id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ status }),
        },
      );

      setTasks((currentTasks) =>
        currentTasks
          .map((task) => (task.id === id ? result.task : task))
          .filter(
            (task) => filter === "ALL" || task.status === filter,
          ),
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to update task status.",
      );
    }
  }

  async function analyse(task: Task) {
    setError("");
    setAnalysingId(task.id);

    try {
      const result = await request<{ analysis: Analysis }>(
        `/tasks/${task.id}/analyse`,
        { method: "POST" },
      );

      setAnalysis((current) => ({
        ...current,
        [task.id]: result.analysis,
      }));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to analyse task.",
      );
    } finally {
      setAnalysingId(null);
    }
  }

  return (
    <main className="app-shell">
      <header className="page-header">
        <div>
          <h1>Task review</h1>
          <p className="subtitle">
            Review incoming work and decide what needs attention.
          </p>
        </div>
      </header>

      <section className="toolbar" aria-label="Task controls">
        <div>
          <strong>{tasks.length}</strong>{" "}
          {tasks.length === 1 ? "task" : "tasks"}
          {filter !== "ALL" && (
            <span className="muted"> · {formatStatus(filter)}</span>
          )}
        </div>
        <label>
          Status
          <select
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value as Filter)
            }
          >
            {filters.map((value) => (
              <option key={value} value={value}>
                {formatStatus(value)}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error && (
        <div className="error" role="alert">
          <strong>Unable to complete request</strong>
          <span>{error}</span>
        </div>
      )}

      {isLoading && <p className="state-message">Loading tasks...</p>}

      {!isLoading && !error && tasks.length === 0 && (
        <p className="state-message">There are no tasks in this view.</p>
      )}

      <section className="task-list" aria-label="Tasks">
        {tasks.map((task) => (
          <article className="task-card" key={task.id}>
            <div className="task-summary">
              <div>
                <div className="task-meta">
                  <span className={`priority ${task.priority.toLowerCase()}`}>
                    {task.priority} priority
                  </span>
                  <time dateTime={task.createdAt}>
                    {new Date(task.createdAt).toLocaleDateString()}
                  </time>
                </div>
                <h2>{task.title}</h2>
                <p className="description">{task.description}</p>
              </div>

              <div className="task-controls">
                <label>
                  <span className="sr-only">Status for {task.title}</span>
                  <select
                    value={task.status}
                    onChange={(event) =>
                      updateStatus(
                        task.id,
                        event.target.value as Status,
                      )
                    }
                  >
                    {filters.slice(1).map((status) => (
                      <option key={status} value={status}>
                        {formatStatus(status)}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="secondary-button"
                  onClick={() => analyse(task)}
                  disabled={analysingId === task.id}
                >
                  {analysingId === task.id
                    ? "Analysing..."
                    : "Analyse task"}
                </button>
              </div>
            </div>

            {analysis[task.id] && (
              <div className="analysis">
                <div className="analysis-title">
                  <strong>Suggested next step</strong>
                  <span>
                    {analysis[task.id].category} ·{" "}
                    {analysis[task.id].priority} priority
                  </span>
                </div>
                <p>{analysis[task.id].summary}</p>
                <p className="recommended-action">
                  {analysis[task.id].recommendedAction}
                </p>
              </div>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
