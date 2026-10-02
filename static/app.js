document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("careerForm");
  if (!form) return;

  const btn = document.getElementById("generateBtn");
  const loading = document.getElementById("loading");
  const errorBox = document.getElementById("formError");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.classList.add("hidden");
    btn.disabled = true;
    btn.innerHTML = "Building your roadmap <span>…</span>";
    form.parentElement.classList.add("hidden");
    loading.classList.remove("hidden");

    const data = Object.fromEntries(new FormData(form).entries());

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.error || "Something went wrong.");
      window.location.href = "/roadmap";
    } catch (err) {
      form.parentElement.classList.remove("hidden");
      loading.classList.add("hidden");
      btn.disabled = false;
      btn.innerHTML = 'Generate my roadmap <span>→</span>';
      errorBox.textContent = err.message;
      errorBox.classList.remove("hidden");
      window.scrollTo({top: form.parentElement.offsetTop - 100, behavior: "smooth"});
    }
  });
});
