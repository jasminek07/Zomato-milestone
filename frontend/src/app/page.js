"use client";

import { useState, useEffect, useRef } from "react";

const API_BASE = "http://127.0.0.1:8000";
const foodEmojis = ["🍕", "🍜", "🍣", "🥘", "🍷", "🥗", "🍱", "🍔", "☕", "🥐"];
const loadingMessages = [
  "Scanning 1,000+ restaurants…",
  "Applying your filters…",
  "Ranking with Groq AI…",
  "Preparing your picks…",
];

export default function Home() {
  // Navigation & Drawer
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("home");

  // Underline state
  const [underlineActive, setUnderlineActive] = useState(false);

  // Floating food emojis
  const [foods, setFoods] = useState([]);

  // Stats count-up animation
  const [statsCount, setStatsCount] = useState({ restaurants: 0, cities: 0 });
  const statsSectionRef = useRef(null);

  // Form selections and options
  const [locations, setLocations] = useState([]);
  const [cuisines, setCuisines] = useState([]);
  const [locationError, setLocationError] = useState("");

  const [formData, setFormData] = useState({
    location: "",
    budget: "medium",
    cuisine: "",
    min_rating: 4.0,
    num_recommendations: 5,
    additional: "",
  });

  // App UI State Machine: 'idle' | 'loading' | 'success' | 'error'
  const [uiState, setUiState] = useState("idle");
  const [loadingText, setLoadingText] = useState(loadingMessages[0]);
  const [errorMessage, setErrorMessage] = useState("");
  const [resultsData, setResultsData] = useState(null);

  // 1. Navigation scroll tracking
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // 2. Animated underline
  useEffect(() => {
    const timer = setTimeout(() => {
      setUnderlineActive(true);
    }, 900);
    return () => clearTimeout(timer);
  }, []);

  // 3. Floating Food Spawn
  useEffect(() => {
    const spawnFood = () => {
      const id = Math.random().toString(36).substring(2, 9);
      const emoji = foodEmojis[Math.floor(Math.random() * foodEmojis.length)];
      const duration = 18 + Math.random() * 18;
      const left = Math.random() * 95; // percent

      setFoods((prev) => [...prev, { id, emoji, duration, left }]);

      setTimeout(() => {
        setFoods((prev) => prev.filter((f) => f.id !== id));
      }, duration * 1000);
    };

    const interval = setInterval(spawnFood, 3200);
    // Initial spawn
    for (let i = 0; i < 5; i++) {
      setTimeout(spawnFood, i * 800);
    }
    return () => clearInterval(interval);
  }, []);

  // 4. Reveal Animation (Intersection Observer)
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("active");
          }
        });
      },
      { threshold: 0.1 }
    );

    const revealElements = document.querySelectorAll(".reveal");
    revealElements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  // 5. Stats Count Up Animation (Intersection Observer)
  useEffect(() => {
    let triggered = false;

    const startCountAnimation = () => {
      let startTimestamp = null;
      const duration = 1500;

      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);

        setStatsCount({
          restaurants: Math.floor(progress * 1000),
          cities: Math.floor(progress * 20),
        });

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          setStatsCount({ restaurants: 1000, cities: 20 });
        }
      };
      requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting && !triggered) {
            triggered = true;
            startCountAnimation();
            observer.unobserve(e.target);
          }
        });
      },
      { threshold: 0.5 }
    );

    if (statsSectionRef.current) {
      observer.observe(statsSectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  // 6. Loading messages cycler
  useEffect(() => {
    if (uiState !== "loading") return;

    let idx = 0;
    const interval = setInterval(() => {
      idx = (idx + 1) % loadingMessages.length;
      setLoadingText(loadingMessages[idx]);
    }, 2000);

    return () => clearInterval(interval);
  }, [uiState]);

  // 7. Load location and cuisine metadata
  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const [locRes, cuiRes] = await Promise.all([
          fetch(`${API_BASE}/meta/locations`),
          fetch(`${API_BASE}/meta/cuisines`),
        ]);

        if (locRes.ok) {
          const { locations } = await locRes.json();
          setLocations(locations);
        } else {
          setLocationError("Error loading locations — is backend running?");
        }

        if (cuiRes.ok) {
          const { cuisines } = await cuiRes.json();
          setCuisines(cuisines);
        }
      } catch (err) {
        console.error("Metadata fetch failed:", err);
        setLocationError("Backend not reachable");
      }
    };

    fetchMeta();
  }, []);

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "min_rating" ? parseFloat(value) : name === "num_recommendations" ? parseInt(value, 10) : value,
    }));
  };

  const handleBudgetChange = (tier) => {
    setFormData((prev) => ({ ...prev, budget: tier }));
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();

    if (!formData.location) {
      // Prompt user to choose location
      alert("Please select a location.");
      return;
    }

    setUiState("loading");
    setLoadingText(loadingMessages[0]);

    if (window.innerWidth < 900) {
      document.getElementById("try-it")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    const payload = {
      location: formData.location,
      budget: formData.budget,
      min_rating: formData.min_rating,
      num_recommendations: formData.num_recommendations,
    };
    if (formData.cuisine) payload.cuisine = formData.cuisine;
    if (formData.additional) payload.additional = formData.additional;

    try {
      const res = await fetch(`${API_BASE}/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok) {
        setResultsData(data);
        setUiState("success");
      } else if (res.status === 404) {
        setErrorMessage(`<strong>No restaurants found!</strong><br/>${data.detail?.summary || ""}<br/><em>Try relaxing your filters.</em>`);
        setUiState("error");
      } else if (res.status === 400) {
        setErrorMessage(`Validation Error: ${data.detail}`);
        setUiState("error");
      } else {
        setErrorMessage(data.detail || "An unexpected error occurred.");
        setUiState("error");
      }
    } catch (err) {
      console.error("API Error:", err);
      setErrorMessage("Failed to connect to the recommendation engine. Ensure the FastAPI server is running on port 8000.");
      setUiState("error");
    }
  };

  return (
    <>
      {/* ── Ambient Background Layer ── */}
      <div className="bg-layer" aria-hidden="true">
        <div className="orb orb-red"></div>
        <div className="orb orb-purple"></div>
        <div className="orb orb-navy"></div>
        <div id="food-container">
          {foods.map((f) => (
            <div
              key={f.id}
              className="floating-food"
              style={{
                left: `${f.left}vw`,
                bottom: "-60px",
                animation: `floatFood ${f.duration}s linear forwards`,
              }}
            >
              {f.emoji}
            </div>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <header className={`nav ${scrolled ? "scrolled" : ""}`} id="main-nav">
        <div className="nav-inner container">
          <a href="#" className="brand" aria-label="Zomato AI Home">
            <span className="material-symbols-outlined brand-icon">restaurant</span>
            <span className="brand-text">Zomato <span className="brand-ai">AI</span></span>
          </a>
          <nav className="nav-links" aria-label="Main navigation">
            <a
              href="#"
              className={`nav-link ${activeSection === "home" ? "active" : ""}`}
              onClick={() => setActiveSection("home")}
            >
              Home
            </a>
            <a
              href="#how-it-works"
              className={`nav-link ${activeSection === "how-it-works" ? "active" : ""}`}
              onClick={() => setActiveSection("how-it-works")}
            >
              How It Works
            </a>
            <a
              href="#features"
              className={`nav-link ${activeSection === "features" ? "active" : ""}`}
              onClick={() => setActiveSection("features")}
            >
              Features
            </a>
            <a
              href="#try-it"
              className={`nav-link ${activeSection === "try-it" ? "active" : ""}`}
              onClick={() => setActiveSection("try-it")}
            >
              Try It
            </a>
          </nav>
          <a href="#try-it" className="btn-pill btn-outline nav-cta">
            Get Recommendations <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>arrow_forward</span>
          </a>
          <button
            className="hamburger"
            id="hamburger-btn"
            aria-label="Open menu"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen((prev) => !prev)}
          >
            <span className="material-symbols-outlined">{drawerOpen ? "close" : "menu"}</span>
          </button>
        </div>

        {/* Mobile drawer */}
        <div className={`mobile-drawer ${drawerOpen ? "open" : ""}`} id="mobile-drawer" aria-hidden={!drawerOpen}>
          <a href="#" className="nav-link" onClick={() => setDrawerOpen(false)}>Home</a>
          <a href="#how-it-works" className="nav-link" onClick={() => setDrawerOpen(false)}>How It Works</a>
          <a href="#features" className="nav-link" onClick={() => setDrawerOpen(false)}>Features</a>
          <a href="#try-it" className="nav-link" onClick={() => setDrawerOpen(false)}>Try It</a>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero" id="home">
        <div className="container hero-inner">
          <div className="pill-badge reveal">🤖 Powered by Groq AI</div>

          <h1 className="hero-title reveal">
            Discover Your<br />
            <span className={`text-primary animated-underline ${underlineActive ? "active" : ""}`} id="hero-underline">
              Perfect Restaurant.
            </span>
          </h1>

          <p className="hero-sub reveal">
            India's smartest dining assistant. Tell us what you're craving, your budget,
            and the vibe — we'll instantly generate the ultimate curated list.
          </p>

          <div className="hero-ctas reveal">
            <a href="#try-it" className="btn-pill btn-primary btn-lg">✨ Find My Restaurant</a>
            <a href="#how-it-works" className="btn-pill btn-ghost btn-lg">▶ How It Works</a>
          </div>

          <div className="hero-stats reveal">
            <div className="stat-badge">🍴 1,000+ Restaurants</div>
            <div className="stat-badge">🏙️ 20+ Cities</div>
            <div className="stat-badge">⚡ Groq LLM Powered</div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="section section-alt" id="how-it-works">
        <div className="container">
          <div className="section-label reveal">THE PROCESS</div>
          <h2 className="section-title reveal">3 Simple Steps to Your Perfect Meal</h2>
          <p className="section-sub reveal">From craving to table in under 10 seconds.</p>

          <div className="steps-grid">
            <div className="step-card glass-panel reveal">
              <div className="step-num">01</div>
              <div className="step-icon">🎯</div>
              <h3 className="step-title">Set Your Preferences</h3>
              <p className="step-body">Choose your city, budget, cuisine type, and minimum rating. Add extra requests in plain language.</p>
            </div>
            <div className="step-arrow reveal">→</div>
            <div className="step-card glass-panel glass-featured reveal">
              <div className="step-num">02</div>
              <div className="step-icon step-icon-glow">🧠</div>
              <h3 className="step-title">AI Filters &amp; Ranks</h3>
              <p className="step-body">Our system narrows 1,000+ restaurants, then Groq's LLM ranks the shortlist and crafts a personalised reason for each pick.</p>
            </div>
            <div className="step-arrow reveal">→</div>
            <div className="step-card glass-panel reveal">
              <div className="step-num">03</div>
              <div className="step-icon step-icon-gold">🏆</div>
              <h3 className="step-title">Get Your Picks</h3>
              <p className="step-body">Receive your top restaurants with AI explanations — ranked, explained, and ready to explore.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="section" id="features">
        <div className="container">
          <div className="section-label reveal">WHY ZOMATO AI</div>
          <h2 className="section-title reveal">More Than Just a Search</h2>

          <div className="features-grid">
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">🎯</div>
              <h3 className="feature-title">Smart Filtering</h3>
              <p className="feature-body">Hard filters on location, budget, cuisine and rating before the LLM ever sees a single restaurant.</p>
            </div>
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">🤖</div>
              <h3 className="feature-title">LLM-Powered Rankings</h3>
              <p className="feature-body">Groq's Llama 3 reads your preferences and ranks restaurants with a human-like explanation for each pick.</p>
            </div>
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">💬</div>
              <h3 className="feature-title">Plain Language Input</h3>
              <p className="feature-body">Add notes like "rooftop seating" or "family-friendly" — the AI understands context, not just keywords.</p>
            </div>
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-title">Results in Seconds</h3>
              <p className="feature-body">Structured filtering keeps the dataset lean. LLM gets a focused shortlist. You get results in under 5 seconds.</p>
            </div>
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">🛡️</div>
              <h3 className="feature-title">No Hallucinations</h3>
              <p className="feature-body">The AI can only recommend restaurants from the real dataset — invented restaurants are automatically rejected.</p>
            </div>
            <div className="feature-card glass-panel reveal">
              <div className="feature-icon">📊</div>
              <h3 className="feature-title">Transparent Metadata</h3>
              <p className="feature-body">See exactly how many restaurants were considered, which filters were applied, and whether AI was used.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Strip */}
      <div className="stats-strip reveal" ref={statsSectionRef}>
        <div className="stat-item">
          <span className="stat-num">{statsCount.restaurants}</span>
          <span className="stat-label">Restaurants</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-num">{statsCount.cities}</span>
          <span className="stat-label">Cities</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-num">&lt;5s</span>
          <span className="stat-label">Response Time</span>
        </div>
        <div className="stat-divider"></div>
        <div className="stat-item">
          <span className="stat-num">100%</span>
          <span className="stat-label">Real Data</span>
        </div>
      </div>

      {/* Live Recommender Tool */}
      <section className="section section-alt" id="try-it">
        <div className="container">
          <div className="section-label reveal">TRY IT NOW</div>
          <h2 className="section-title reveal">Find Your Restaurant</h2>
          <p className="section-sub reveal">Powered by real Zomato data + Groq AI. Results in seconds.</p>

          <div className="tool-layout">
            {/* Form Panel */}
            <div className="form-panel glass-panel-heavy reveal">
              <h3 className="form-panel-title">✨ Your Preferences</h3>

              <form onSubmit={handleFormSubmit} noValidate>
                <div className="form-group">
                  <label className="form-label" htmlFor="location">
                    Location <span className="required">*</span>
                  </label>
                  <div className="select-wrapper">
                    <select
                      id="location"
                      name="location"
                      required
                      value={formData.location}
                      onChange={handleFormChange}
                    >
                      <option value="" disabled>
                        {locationError || "Select a city…"}
                      </option>
                      {locations.map((loc) => (
                        <option key={loc} value={loc}>
                          {loc}
                        </option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined select-icon">location_on</span>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Budget Tier <span className="required">*</span>
                  </label>
                  <div className="budget-group">
                    {["low", "medium", "high"].map((tier) => (
                      <label
                        key={tier}
                        className={`budget-card ${formData.budget === tier ? "selected" : ""}`}
                        onClick={() => handleBudgetChange(tier)}
                      >
                        <input
                          type="radio"
                          name="budget"
                          value={tier}
                          checked={formData.budget === tier}
                          onChange={() => {}}
                        />
                        <span>
                          {tier === "low" && "₹ Low"}
                          {tier === "medium" && "₹₹ Medium"}
                          {tier === "high" && "₹₹₹ High"}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="cuisine">
                    Cuisine <span className="optional">(optional)</span>
                  </label>
                  <div className="select-wrapper">
                    <select
                      id="cuisine"
                      name="cuisine"
                      value={formData.cuisine}
                      onChange={handleFormChange}
                    >
                      <option value="">Any Cuisine</option>
                      {cuisines.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined select-icon">restaurant_menu</span>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="min_rating">
                    Minimum Rating
                    <span id="rating-value" className="rating-display">
                      {formData.min_rating.toFixed(1)} ⭐
                    </span>
                  </label>
                  <input
                    type="range"
                    id="min_rating"
                    name="min_rating"
                    min="0"
                    max="5"
                    step="0.1"
                    value={formData.min_rating}
                    onChange={handleFormChange}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="num_recommendations">
                    Recommendations
                  </label>
                  <div className="select-wrapper">
                    <select
                      id="num_recommendations"
                      name="num_recommendations"
                      value={formData.num_recommendations}
                      onChange={handleFormChange}
                    >
                      <option value="3">3 Restaurants</option>
                      <option value="5">5 Restaurants</option>
                      <option value="7">7 Restaurants</option>
                      <option value="10">10 Restaurants</option>
                    </select>
                    <span className="material-symbols-outlined select-icon">format_list_numbered</span>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="additional">
                    Additional Requests <span className="optional">(optional)</span>
                  </label>
                  <textarea
                    id="additional"
                    name="additional"
                    rows="2"
                    placeholder="e.g. rooftop seating, vegan options, quick service…"
                    value={formData.additional}
                    onChange={handleFormChange}
                  ></textarea>
                </div>

                <button
                  type="submit"
                  id="submit-btn"
                  className="btn-pill btn-primary btn-lg btn-full"
                  disabled={uiState === "loading"}
                >
                  ✨ Find My Restaurant
                </button>
              </form>
            </div>

            {/* Results Panel */}
            <div className="results-panel">
              {/* Idle State */}
              {uiState === "idle" && (
                <div id="idle-state" className="state-box state-idle active">
                  <div className="idle-icon">🍽️</div>
                  <h3 className="state-title">What are you craving?</h3>
                  <p className="state-sub">Fill in your preferences and let AI find your perfect restaurant.</p>
                </div>
              )}

              {/* Loading State */}
              {uiState === "loading" && (
                <div id="loading-state" className="state-box state-loading active">
                  <div className="spinner-ring"></div>
                  <h3 className="state-title">Consulting the AI Chef…</h3>
                  <p className="state-sub" id="loading-text">
                    {loadingText}
                  </p>
                </div>
              )}

              {/* Error State */}
              {uiState === "error" && (
                <div id="error-state" className="state-box state-error active">
                  <div className="error-icon-wrap">⚠️</div>
                  <p id="error-message" className="state-sub" dangerouslySetInnerHTML={{ __html: errorMessage }}></p>
                  <button className="btn-pill btn-outline" onClick={() => setUiState("idle")}>
                    Try Again
                  </button>
                </div>
              )}

              {/* Success State */}
              {uiState === "success" && resultsData && (
                <div id="success-state" className="state-box state-success active">
                  <div id="summary-banner" className="summary-banner glass-panel">
                    {resultsData.summary || "Here are your recommended restaurants."}
                  </div>
                  <div id="meta-banner" className="meta-banner">
                    <span className="meta-pill">
                      📊 Candidates: <b>{resultsData.meta?.candidates_considered}</b>
                    </span>
                    <span className={`meta-pill ${resultsData.meta?.llm_used ? "green" : "amber"}`}>
                      🤖 AI Ranked: <b>{resultsData.meta?.llm_used ? "Yes" : "Fallback"}</b>
                    </span>
                    {resultsData.meta?.filters_relaxed && resultsData.meta.filters_relaxed.length > 0 && (
                      <span className="meta-pill red">
                        ⚠️ Filters Relaxed: {resultsData.meta.filters_relaxed.join(", ")}
                      </span>
                    )}
                  </div>
                  <div id="recommendations-list" className="rec-list">
                    {resultsData.recommendations?.map((rec, i) => {
                      const isFirst = rec.rank === 1;
                      const cuisineTags = rec.cuisine
                        ? rec.cuisine.split(",").map((c) => c.trim())
                        : [];

                      return (
                        <div
                          key={rec.restaurant_name + i}
                          className={`rec-card ${isFirst ? "rank-1" : "rank-other"}`}
                          style={{ animationDelay: `${i * 0.1}s` }}
                        >
                          <div className={`rec-rank-badge ${isFirst ? "badge-gold" : "badge-red"}`}>
                            #{rec.rank}
                          </div>
                          <div className="rec-content">
                            <div className="rec-header">
                              <div className="rec-name">{rec.restaurant_name}</div>
                              <div className="rec-rating">{rec.rating} ⭐</div>
                            </div>
                            <div className="rec-tags">
                              {cuisineTags.map((c) => (
                                <span key={c} className="rec-tag">
                                  {c}
                                </span>
                              ))}
                              <span className="rec-tag cost">💰 {rec.estimated_cost}</span>
                            </div>
                            <div className="rec-divider"></div>
                            <div className="rec-ai-note">
                              <span className="rec-ai-icon">🤖</span>
                              <p className="rec-explanation">{rec.explanation}</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="cta-banner reveal">
        <div className="container cta-inner">
          <h2 className="cta-title">Ready to Find Your Next Favourite Restaurant?</h2>
          <p className="cta-sub">Join thousands of food lovers discovering hidden gems with AI.</p>
          <a href="#try-it" className="btn-pill btn-white btn-lg">✨ Try It Now</a>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container footer-grid">
          <div className="footer-col">
            <div className="footer-brand">🍽️ Zomato AI</div>
            <p className="footer-tagline">AI-powered restaurant discovery for India.</p>
            <div className="tech-pills">
              <span className="tech-pill">🐍 FastAPI</span>
              <span className="tech-pill">🤗 HuggingFace</span>
              <span className="tech-pill">⚡ Groq</span>
              <span className="tech-pill">⚛️ Next.js (React)</span>
            </div>
          </div>
          <div className="footer-col">
            <span className="footer-heading">Navigate</span>
            <a href="#" className="footer-link">Home</a>
            <a href="#how-it-works" className="footer-link">How It Works</a>
            <a href="#features" className="footer-link">Features</a>
            <a href="#try-it" className="footer-link">Try It</a>
          </div>
          <div className="footer-col">
            <span className="footer-heading">Tech Stack</span>
            <span className="footer-link">Python 3.9 + FastAPI</span>
            <span className="footer-link">Hugging Face Dataset</span>
            <span className="footer-link">Groq Llama 3</span>
            <span className="footer-link">Next.js 15 (App Router)</span>
          </div>
        </div>
        <div className="footer-bottom container">
          © 2025 Zomato AI · Built for the AI Milestone Project
        </div>
      </footer>
    </>
  );
}
