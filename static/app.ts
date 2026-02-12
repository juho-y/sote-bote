interface SummaryData {
  summary: string;
  key_points: string[];
  language: string;
}

const STORAGE_KEY = "sote_bote_summary";

function saveSummaryToStorage(data: SummaryData): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error("Failed to save to localStorage:", error);
  }
}

function loadSummaryFromStorage(): SummaryData | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.error("Failed to load from localStorage:", error);
    return null;
  }
}

function displaySummary(data: SummaryData): void {
  clearPlaceholder();
  document.getElementById("summary")!.textContent = data.summary;

  const keypointsDiv = document.getElementById("keypoints")!;
  if (data.key_points && data.key_points.length > 0) {
    const ol = document.createElement("ol");
    data.key_points.forEach((point) => {
      const li = document.createElement("li");
      li.textContent = point;
      ol.appendChild(li);
    });
    keypointsDiv.innerHTML = "<h4>Key Points:</h4>";
    keypointsDiv.appendChild(ol);
  } else {
    keypointsDiv.innerHTML = "";
  }

  saveSummaryToStorage(data);
}

function showError(message: string): void {
  document.getElementById("error-message")!.textContent = message;
  document.getElementById("error-box")!.style.display = "block";
  const summaryEl = document.getElementById("summary")!;
  summaryEl.className = "";
  summaryEl.textContent = "";
  document.getElementById("keypoints")!.innerHTML = "";
}

function hideError(): void {
  document.getElementById("error-box")!.style.display = "none";
}

function showPlaceholder(): void {
  const summaryEl = document.getElementById("summary")!;
  summaryEl.textContent =
    'No summary yet. Paste your transcript above and click "Summarize" to get started.';
  summaryEl.className = "placeholder";
}

function clearPlaceholder(): void {
  const summaryEl = document.getElementById("summary")!;
  summaryEl.className = "";
}

function showLoading(): void {
  const summaryEl = document.getElementById("summary")!;
  summaryEl.className = "";
  summaryEl.innerHTML =
    '<div class="loading"><div class="spinner"></div><span>Summarizing your transcript...</span></div>';
}

async function loadExistingSummary(): Promise<void> {
  try {
    const response = await fetch("/summary", {
      credentials: "same-origin",
    });

    const data: SummaryData = await response.json();

    if (data.summary) {
      displaySummary(data);
      (document.getElementById("language") as HTMLSelectElement).value =
        data.language;
    } else {
      // NB; Fallback to localStorage, not ideal due to the extra complexity of maintaining two sources of truth.
      const cachedData = loadSummaryFromStorage();
      if (cachedData && cachedData.summary) {
        displaySummary(cachedData);
        (document.getElementById("language") as HTMLSelectElement).value =
          cachedData.language;
      } else {
        showPlaceholder();
      }
    }
  } catch (error) {
    console.error("Error loading summary:", error);
    const cachedData = loadSummaryFromStorage();
    if (cachedData && cachedData.summary) {
      displaySummary(cachedData);
      (document.getElementById("language") as HTMLSelectElement).value =
        cachedData.language;
    } else {
      showPlaceholder();
    }
  }
}

loadExistingSummary();

async function summarize(): Promise<void> {
  const text = (document.getElementById("transcript") as HTMLTextAreaElement)
    .value;
  const language = (document.getElementById("language") as HTMLSelectElement)
    .value;

  if (!text.trim()) {
    showError("Please enter some text to summarize");
    return;
  }

  hideError();
  showLoading();
  document.getElementById("keypoints")!.innerHTML = "";

  try {
    const response = await fetch("/summarize", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        language: language,
      }),
    });

    const data: SummaryData = await response.json();

    if (!response.ok) {
      showError((data as any).detail || "Failed to summarize the text");
      return;
    }

    displaySummary(data);
  } catch (error) {
    console.error("Summarization error:", error);
    showError("Network error: " + (error as Error).message);
  }
}

(window as any).summarize = summarize;
