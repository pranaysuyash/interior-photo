/**
 * Analytics Service for Interior AI
 *
 * Integrates with:
 * - Google Analytics 4
 * - Mixpanel
 * - Custom event tracking
 */

interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
}

class AnalyticsService {
  private enabled: boolean;
  private gaId: string | undefined;
  private mixpanelToken: string | undefined;

  constructor() {
    this.enabled = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';
    this.gaId = import.meta.env.VITE_GA_TRACKING_ID;
    this.mixpanelToken = import.meta.env.VITE_MIXPANEL_TOKEN;

    if (this.enabled) {
      this.initialize();
    }
  }

  private initialize() {
    // Initialize Google Analytics
    if (this.gaId && typeof window !== 'undefined') {
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${this.gaId}`;
      document.head.appendChild(script);

      (window as any).dataLayer = (window as any).dataLayer || [];
      function gtag(...args: any[]) {
        (window as any).dataLayer.push(arguments);
      }
      (window as any).gtag = gtag;

      gtag('js', new Date());
      gtag('config', this.gaId);
    }

    // Initialize Mixpanel
    if (this.mixpanelToken && typeof window !== 'undefined') {
      // Mixpanel initialization code would go here
      console.log('Mixpanel initialized with token:', this.mixpanelToken);
    }
  }

  /**
   * Track a page view
   */
  pageView(path: string, title?: string) {
    if (!this.enabled) return;

    // Google Analytics
    if (this.gaId && (window as any).gtag) {
      (window as any).gtag('config', this.gaId, {
        page_path: path,
        page_title: title
      });
    }

    // Mixpanel
    if (this.mixpanelToken && (window as any).mixpanel) {
      (window as any).mixpanel.track('Page View', {
        path,
        title
      });
    }
  }

  /**
   * Track a custom event
   */
  track(event: string, properties?: Record<string, any>) {
    if (!this.enabled) return;

    // Google Analytics
    if ((window as any).gtag) {
      (window as any).gtag('event', event, properties);
    }

    // Mixpanel
    if ((window as any).mixpanel) {
      (window as any).mixpanel.track(event, properties);
    }

    // Console in development
    if (import.meta.env.DEV) {
      console.log('📊 Analytics Event:', event, properties);
    }
  }

  /**
   * Identify a user
   */
  identify(userId: string, traits?: Record<string, any>) {
    if (!this.enabled) return;

    // Google Analytics
    if ((window as any).gtag) {
      (window as any).gtag('set', { user_id: userId });
      if (traits) {
        (window as any).gtag('set', 'user_properties', traits);
      }
    }

    // Mixpanel
    if ((window as any).mixpanel) {
      (window as any).mixpanel.identify(userId);
      if (traits) {
        (window as any).mixpanel.people.set(traits);
      }
    }
  }

  /**
   * Track user signup
   */
  trackSignup(method: string = 'email') {
    this.track('signup', {
      method,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track user login
   */
  trackLogin(method: string = 'email') {
    this.track('login', {
      method,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track transformation creation
   */
  trackTransformationStart(vibe: string, colors: string, hasReferences: boolean) {
    this.track('transformation_started', {
      vibe,
      colors,
      has_references: hasReferences,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track transformation completion
   */
  trackTransformationComplete(transformationId: string, processingTime: number) {
    this.track('transformation_completed', {
      transformation_id: transformationId,
      processing_time_seconds: processingTime,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track transformation failure
   */
  trackTransformationError(error: string) {
    this.track('transformation_error', {
      error_message: error,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track image download
   */
  trackDownload(transformationId: string) {
    this.track('image_downloaded', {
      transformation_id: transformationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track credit purchase
   */
  trackCreditPurchase(pack: string, amount: number) {
    this.track('credit_purchased', {
      pack,
      amount_usd: amount / 100,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track subscription
   */
  trackSubscription(plan: string, interval: 'monthly' | 'yearly') {
    this.track('subscription_started', {
      plan,
      interval,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track feature usage
   */
  trackFeatureUse(feature: string) {
    this.track('feature_used', {
      feature,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Track errors
   */
  trackError(error: Error, context?: string) {
    this.track('error', {
      error_name: error.name,
      error_message: error.message,
      error_stack: error.stack,
      context,
      timestamp: new Date().toISOString()
    });
  }
}

// Global instance
export const analytics = new AnalyticsService();
