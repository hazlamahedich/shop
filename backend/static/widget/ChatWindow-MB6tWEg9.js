import { j as jsxRuntimeExports, r as reactExports, u as useReducedMotion, D as DEFAULT_CAROUSEL_CONFIG, t as trackCarouselEngagement, l as logContactInteraction, a as DEFAULT_VOICE_CONFIG, b as trackVoiceInput, c as trackMessageSend, f as formatRetryTime, E as ErrorSeverity, w as widgetClient, W as WidgetApiException, d as trackQuickReplyClick, F as FocusTrap, T as ThemeToggle } from "./loader-DmBM3hj-.js";
function ProductCard({ product, theme, onAddToCart, onClick, isAdding }) {
  const handleCardClick = () => {
    if (onClick && product.available) {
      onClick(product);
    }
  };
  const handleKeyDown = (e) => {
    if ((e.key === "Enter" || e.key === " ") && onClick && product.available) {
      e.preventDefault();
      onClick(product);
    }
  };
  const handleAddToCart = (e) => {
    e.stopPropagation();
    if (onAddToCart && product.available) {
      onAddToCart(product);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "product-card",
      onClick: handleCardClick,
      onKeyDown: handleKeyDown,
      tabIndex: onClick ? 0 : void 0,
      role: onClick ? "button" : void 0,
      "aria-label": onClick ? `View details for ${product.title}` : void 0,
      style: {
        display: "flex",
        gap: 12,
        padding: 12,
        backgroundColor: "#ffffff",
        borderRadius: 12,
        border: product.isPinned ? `2px solid ${theme.primaryColor}` : "1px solid #e5e7eb",
        marginBottom: 8,
        cursor: onClick ? "pointer" : "default",
        transition: "box-shadow 0.2s, border-color 0.2s",
        position: "relative"
      },
      children: [
        product.isPinned && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "featured-badge",
            style: {
              position: "absolute",
              top: -8,
              left: 8,
              background: theme.primaryColor,
              color: "white",
              padding: "2px 8px",
              borderRadius: 4,
              fontSize: 10,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 3,
              boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              zIndex: 1
            },
            children: "⭐ Featured"
          }
        ),
        product.imageUrl && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "img",
          {
            src: product.imageUrl,
            alt: product.title,
            style: {
              width: 64,
              height: 64,
              objectFit: "cover",
              borderRadius: 8,
              flexShrink: 0
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: 0 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontWeight: 500,
                fontSize: 13,
                marginBottom: 4,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              },
              children: product.title
            }
          ),
          product.productType && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontSize: 11,
                color: "#6b7280",
                marginBottom: 4
              },
              children: product.productType
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 600, fontSize: 14 }, children: [
                  "$",
                  (product.price ?? 0).toFixed(2)
                ] }),
                onAddToCart && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleAddToCart,
                    disabled: !product.available || isAdding,
                    style: {
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 500,
                      backgroundColor: product.available ? theme.primaryColor : "#9ca3af",
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      cursor: product.available ? "pointer" : "not-allowed",
                      opacity: isAdding ? 0.7 : 1
                    },
                    children: isAdding ? "Adding..." : product.available ? "Add to Cart" : "Sold Out"
                  }
                )
              ]
            }
          )
        ] })
      ]
    }
  );
}
function ProductList({ products, theme, onAddToCart, onProductClick, addingProductId }) {
  if (products.length === 0) {
    return null;
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "product-list", style: { marginTop: 8 }, children: products.map((product) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    ProductCard,
    {
      product,
      theme,
      onAddToCart,
      onClick: onProductClick,
      isAdding: addingProductId === product.id
    },
    product.id
  )) });
}
function useRipple() {
  const [ripples, setRipples] = reactExports.useState([]);
  const createRipple = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const id = Date.now();
    setRipples((prev) => [...prev, { x, y, id }]);
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== id));
    }, 600);
  };
  return { ripples, createRipple };
}
function ProductCardCompact({
  product,
  theme,
  onAddToCart,
  onClick,
  isAdding,
  cardWidth
}) {
  const [imageLoaded, setImageLoaded] = reactExports.useState(false);
  const [imageError, setImageError] = reactExports.useState(false);
  const { ripples, createRipple } = useRipple();
  const reducedMotion = useReducedMotion();
  const handleCardClick = () => {
    if (onClick && product.available) {
      onClick(product);
    }
  };
  const handleKeyDown = (e) => {
    if ((e.key === "Enter" || e.key === " ") && onClick && product.available) {
      e.preventDefault();
      onClick(product);
    }
  };
  const handleAddToCart = (e) => {
    e.stopPropagation();
    if (onAddToCart && product.available) {
      createRipple(e);
      onAddToCart(product);
    }
  };
  const handleImageLoad = () => {
    setImageLoaded(true);
  };
  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(true);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "carousel-card",
      "data-testid": `carousel-card-${product.id}`,
      onClick: handleCardClick,
      onKeyDown: handleKeyDown,
      tabIndex: onClick ? 0 : void 0,
      role: "group",
      "aria-label": `${product.title}, $${(product.price ?? 0).toFixed(2)}`,
      style: {
        width: cardWidth
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "carousel-card-image", "data-testid": `carousel-card-image-${product.id}`, children: [
          !imageLoaded && !imageError && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "carousel-card-skeleton", "data-testid": "carousel-card-skeleton", "aria-hidden": "true" }),
          product.imageUrl && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "img",
            {
              src: product.imageUrl,
              alt: product.title,
              className: imageLoaded ? "" : "loading",
              onLoad: handleImageLoad,
              onError: handleImageError,
              loading: "lazy"
            }
          ),
          imageError && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "var(--widget-skeleton-bg, #f1f5f9)",
                color: "var(--widget-text-muted, #94a3b8)",
                fontSize: 24
              },
              "aria-hidden": "true",
              children: "📦"
            }
          ),
          product.isPinned && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                position: "absolute",
                top: 4,
                left: 4,
                background: theme.primaryColor,
                color: "white",
                padding: "2px 6px",
                borderRadius: 4,
                fontSize: 10,
                fontWeight: 600,
                zIndex: 1
              },
              "aria-label": "Featured product",
              children: "⭐"
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "carousel-card-content", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: "carousel-card-title", children: product.title }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "carousel-card-price", children: [
            "$",
            (product.price ?? 0).toFixed(2)
          ] }),
          onAddToCart && /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              type: "button",
              className: "carousel-card-button",
              "data-testid": `carousel-card-button-${product.id}`,
              onClick: handleAddToCart,
              disabled: !product.available || isAdding,
              "aria-label": isAdding ? "Adding to cart" : product.available ? `Add ${product.title} to cart` : "Sold out",
              style: {
                position: "relative",
                overflow: "hidden"
              },
              children: [
                isAdding ? "Adding..." : product.available ? "Add to Cart" : "Sold Out",
                ripples.map((ripple) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "span",
                  {
                    "data-testid": "ripple-effect",
                    style: {
                      position: "absolute",
                      left: ripple.x,
                      top: ripple.y,
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      backgroundColor: "rgba(255, 255, 255, 0.3)",
                      transform: "translate(-50%, -50%)",
                      pointerEvents: "none",
                      animationName: reducedMotion ? "none" : "ripple",
                      animationDuration: reducedMotion ? "0ms" : "600ms",
                      animationTimingFunction: "ease-out",
                      animationFillMode: "forwards"
                    }
                  },
                  ripple.id
                ))
              ]
            }
          )
        ] })
      ]
    }
  );
}
function CarouselArrows({ onPrev, onNext, canScrollLeft, canScrollRight, theme: _theme }) {
  const handlePrevClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (canScrollLeft) {
      onPrev();
    }
  };
  const handleNextClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (canScrollRight) {
      onNext();
    }
  };
  const handlePrevKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (canScrollLeft) {
        onPrev();
      }
    }
  };
  const handleNextKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (canScrollRight) {
        onNext();
      }
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "carousel-arrows", "data-testid": "carousel-arrows", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        type: "button",
        className: "carousel-arrow carousel-arrow-left",
        "data-testid": "carousel-arrow-left",
        onClick: handlePrevClick,
        onKeyDown: handlePrevKeyDown,
        disabled: !canScrollLeft,
        "aria-label": "Scroll left to previous products",
        title: "Previous",
        children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "15 18 9 12 15 6" }) })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        type: "button",
        className: "carousel-arrow carousel-arrow-right",
        "data-testid": "carousel-arrow-right",
        onClick: handleNextClick,
        onKeyDown: handleNextKeyDown,
        disabled: !canScrollRight,
        "aria-label": "Scroll right to next products",
        title: "Next",
        children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", children: /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "9 18 15 12 9 6" }) })
      }
    )
  ] });
}
function CarouselDots({ totalDots, activeIndex, onDotClick, theme: _theme }) {
  if (totalDots <= 1) {
    return null;
  }
  const handleDotClick = (index) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    onDotClick(index);
  };
  const handleDotKeyDown = (index) => (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onDotClick(index);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "carousel-dots", "data-testid": "carousel-dots", role: "tablist", "aria-label": "Carousel pages", children: Array.from({ length: totalDots }, (_, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "button",
    {
      type: "button",
      className: `carousel-dot ${index === activeIndex ? "active" : ""}`,
      "data-testid": `carousel-dot-${index}`,
      "data-active": index === activeIndex,
      onClick: handleDotClick(index),
      onKeyDown: handleDotKeyDown(index),
      role: "tab",
      "aria-selected": index === activeIndex,
      "aria-label": `Page ${index + 1} of ${totalDots}`,
      tabIndex: index === activeIndex ? 0 : -1
    },
    index
  )) });
}
function useCarousel({ itemCount, config, isMobile = false }) {
  const carouselRef = reactExports.useRef(null);
  const mergedConfig = { ...DEFAULT_CAROUSEL_CONFIG, ...config };
  const visibleCards = isMobile ? mergedConfig.visibleCards.mobile : mergedConfig.visibleCards.desktop;
  const [state, setState] = reactExports.useState({
    activeIndex: 0,
    canScrollLeft: false,
    canScrollRight: itemCount > visibleCards,
    totalDots: Math.ceil(itemCount / visibleCards)
  });
  const calculateCardWidth = reactExports.useCallback(() => {
    if (!carouselRef.current) return mergedConfig.cardWidth;
    const containerWidth = carouselRef.current.clientWidth;
    const totalGaps = (visibleCards - 1) * mergedConfig.cardGap;
    return (containerWidth - totalGaps) / visibleCards;
  }, [visibleCards, mergedConfig.cardGap, mergedConfig.cardWidth]);
  const scrollToIndex = reactExports.useCallback(
    (index) => {
      if (!carouselRef.current) return;
      const cardWidth = calculateCardWidth();
      const scrollPosition = index * (cardWidth + mergedConfig.cardGap);
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      carouselRef.current.scrollTo({
        left: scrollPosition,
        behavior: prefersReducedMotion ? "auto" : "smooth"
      });
    },
    [calculateCardWidth, mergedConfig.cardGap]
  );
  const scrollPrev = reactExports.useCallback(() => {
    const newIndex = Math.max(0, state.activeIndex - 1);
    scrollToIndex(newIndex);
  }, [state.activeIndex, scrollToIndex]);
  const scrollNext = reactExports.useCallback(() => {
    const newIndex = Math.min(itemCount - 1, state.activeIndex + 1);
    scrollToIndex(newIndex);
  }, [itemCount, state.activeIndex, scrollToIndex]);
  const updateScrollState = reactExports.useCallback(() => {
    if (!carouselRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = carouselRef.current;
    const cardWidth = calculateCardWidth();
    const cardWithGap = cardWidth + mergedConfig.cardGap;
    const activeIndex = Math.round(scrollLeft / cardWithGap);
    const maxScroll = scrollWidth - clientWidth;
    setState((prev) => ({
      ...prev,
      activeIndex: Math.max(0, Math.min(activeIndex, itemCount - 1)),
      canScrollLeft: scrollLeft > 5,
      canScrollRight: scrollLeft < maxScroll - 5,
      totalDots: Math.ceil(itemCount / visibleCards)
    }));
  }, [calculateCardWidth, mergedConfig.cardGap, itemCount, visibleCards]);
  reactExports.useEffect(() => {
    const carousel = carouselRef.current;
    if (!carousel) return;
    let timeoutId;
    const handleScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateScrollState, 100);
    };
    carousel.addEventListener("scroll", handleScroll, { passive: true });
    updateScrollState();
    return () => {
      clearTimeout(timeoutId);
      carousel.removeEventListener("scroll", handleScroll);
    };
  }, [updateScrollState]);
  reactExports.useEffect(() => {
    updateScrollState();
  }, [itemCount, visibleCards, updateScrollState]);
  return {
    carouselRef,
    activeIndex: state.activeIndex,
    canScrollLeft: state.canScrollLeft,
    canScrollRight: state.canScrollRight,
    totalDots: state.totalDots,
    scrollToIndex,
    scrollPrev,
    scrollNext
  };
}
function ProductCarousel({
  products,
  theme,
  onAddToCart,
  onProductClick,
  addingProductId,
  config
}) {
  const [isMobile, setIsMobile] = reactExports.useState(false);
  const mergedConfig = { ...DEFAULT_CAROUSEL_CONFIG, ...config };
  reactExports.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);
  const { carouselRef, activeIndex, canScrollLeft, canScrollRight, totalDots, scrollToIndex, scrollPrev, scrollNext } = useCarousel({
    itemCount: products.length,
    config: mergedConfig,
    isMobile
  });
  const visibleCards = isMobile ? mergedConfig.visibleCards.mobile : mergedConfig.visibleCards.desktop;
  const calculateCardWidth = reactExports.useCallback(() => {
    if (!carouselRef.current) return mergedConfig.cardWidth;
    const containerWidth = carouselRef.current.clientWidth;
    const totalGaps = (visibleCards - 1) * mergedConfig.cardGap;
    return Math.floor((containerWidth - totalGaps) / visibleCards);
  }, [visibleCards, mergedConfig.cardGap, mergedConfig.cardWidth]);
  const [cardWidth, setCardWidth] = reactExports.useState(mergedConfig.cardWidth);
  reactExports.useEffect(() => {
    const updateCardWidth = () => {
      setCardWidth(calculateCardWidth());
    };
    updateCardWidth();
    window.addEventListener("resize", updateCardWidth);
    return () => window.removeEventListener("resize", updateCardWidth);
  }, [calculateCardWidth]);
  const handleKeyDown = (e) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      trackCarouselEngagement("swipe");
      scrollPrev();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      trackCarouselEngagement("swipe");
      scrollNext();
    } else if (e.key === "Home") {
      e.preventDefault();
      scrollToIndex(0);
    } else if (e.key === "End") {
      e.preventDefault();
      scrollToIndex(products.length - 1);
    }
  };
  const handleProductClick = (product) => {
    trackCarouselEngagement("click", product.id);
    onProductClick == null ? void 0 : onProductClick(product);
  };
  const handleAddToCart = (product) => {
    trackCarouselEngagement("add_to_cart", product.id);
    onAddToCart == null ? void 0 : onAddToCart(product);
  };
  if (products.length === 0) {
    return null;
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "product-carousel-wrapper",
      "data-testid": "product-carousel-wrapper",
      role: "region",
      "aria-label": `Product carousel with ${products.length} products`,
      "aria-roledescription": "carousel",
      onKeyDown: handleKeyDown,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            ref: carouselRef,
            className: "product-carousel",
            "data-testid": "product-carousel",
            role: "group",
            "aria-label": `${products.length} products`,
            tabIndex: 0,
            children: products.map((product, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                role: "group",
                "aria-label": `${index + 1} of ${products.length}: ${product.title}`,
                "aria-roledescription": "slide",
                children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                  ProductCardCompact,
                  {
                    product,
                    theme,
                    onAddToCart: handleAddToCart,
                    onClick: handleProductClick,
                    isAdding: addingProductId === product.id,
                    cardWidth
                  }
                )
              },
              product.id
            ))
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          CarouselArrows,
          {
            onPrev: scrollPrev,
            onNext: scrollNext,
            canScrollLeft,
            canScrollRight,
            theme
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          CarouselDots,
          {
            totalDots,
            activeIndex: Math.floor(activeIndex / visibleCards),
            onDotClick: (index) => scrollToIndex(index * visibleCards),
            theme
          }
        )
      ]
    }
  );
}
function CartView({
  cart,
  theme,
  onRemoveItem,
  onCheckout,
  isCheckingOut,
  removingItemId
}) {
  if (cart.items.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "cart-view cart-view--empty",
        style: {
          padding: 16,
          textAlign: "center",
          color: "#6b7280",
          fontSize: 13
        },
        children: "Your cart is empty"
      }
    );
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "cart-view",
      style: {
        backgroundColor: "#f9fafb",
        borderRadius: 12,
        padding: 12,
        marginTop: 8
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              fontSize: 13,
              fontWeight: 600,
              marginBottom: 12,
              display: "flex",
              alignItems: "center",
              gap: 8
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  width: "16",
                  height: "16",
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "9", cy: "21", r: "1" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "20", cy: "21", r: "1" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" })
                  ]
                }
              ),
              "Your Cart (",
              cart.itemCount,
              " ",
              cart.itemCount === 1 ? "item" : "items",
              ")"
            ]
          }
        ),
        cart.items.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          CartItemView,
          {
            item,
            onRemove: onRemoveItem,
            isRemoving: removingItemId === item.variantId
          },
          item.variantId
        )),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 12,
              paddingTop: 12,
              borderTop: "1px solid #e5e7eb"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 600 }, children: [
                "Total: $",
                (cart.total ?? 0).toFixed(2)
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: 8 }, children: [
                cart.shopifyCartUrl && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                  "a",
                  {
                    href: cart.shopifyCartUrl,
                    target: "_blank",
                    rel: "noopener noreferrer",
                    style: {
                      padding: "8px 16px",
                      fontSize: 13,
                      fontWeight: 500,
                      backgroundColor: "transparent",
                      color: theme.primaryColor,
                      border: `1px solid ${theme.primaryColor}`,
                      borderRadius: 8,
                      textDecoration: "none",
                      display: "flex",
                      alignItems: "center",
                      gap: 4
                    },
                    children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsxs(
                        "svg",
                        {
                          width: "14",
                          height: "14",
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor",
                          strokeWidth: "2",
                          strokeLinecap: "round",
                          strokeLinejoin: "round",
                          children: [
                            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" }),
                            /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "15 3 21 3 21 9" }),
                            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "10", y1: "14", x2: "21", y2: "3" })
                          ]
                        }
                      ),
                      "View on Store"
                    ]
                  }
                ),
                onCheckout && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: onCheckout,
                    disabled: isCheckingOut,
                    style: {
                      padding: "8px 16px",
                      fontSize: 13,
                      fontWeight: 500,
                      backgroundColor: theme.primaryColor,
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      cursor: "pointer",
                      opacity: isCheckingOut ? 0.7 : 1
                    },
                    children: isCheckingOut ? "Processing..." : "Checkout"
                  }
                )
              ] })
            ]
          }
        )
      ]
    }
  );
}
function CartItemView({ item, onRemove, isRemoving }) {
  const handleRemove = () => {
    if (onRemove && item.variantId) {
      onRemove(item.variantId);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: "cart-item",
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 0",
        borderBottom: "1px solid #e5e7eb"
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { flex: 1, minWidth: 0 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                fontSize: 13,
                fontWeight: 500,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              },
              children: item.title
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: 12, color: "#6b7280" }, children: [
            "Qty: ",
            item.quantity,
            " × $",
            (item.price ?? 0).toFixed(2)
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontWeight: 500, fontSize: 13 }, children: [
            "$",
            ((item.price ?? 0) * item.quantity).toFixed(2)
          ] }),
          onRemove && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: handleRemove,
              disabled: isRemoving,
              style: {
                padding: 4,
                background: "none",
                border: "none",
                cursor: "pointer",
                opacity: isRemoving ? 0.5 : 1
              },
              "aria-label": `Remove ${item.title}`,
              children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  width: "16",
                  height: "16",
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "#ef4444",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "3 6 5 6 21 6" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" })
                  ]
                }
              )
            }
          )
        ] })
      ]
    }
  );
}
function MessageAvatar({
  sender,
  botName,
  theme,
  size = 32
}) {
  const displayName = sender === "merchant" ? "Merchant" : botName;
  const initials = displayName.slice(0, 2).toUpperCase();
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      "data-testid": "message-avatar",
      "aria-label": `${displayName} avatar`,
      role: "img",
      style: {
        width: size,
        height: size,
        borderRadius: "50%",
        backgroundColor: theme.primaryColor,
        color: "white",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: size * 0.4,
        fontWeight: 600,
        flexShrink: 0
      },
      children: initials
    }
  );
}
const formatScore = (score) => {
  return `${Math.round(score * 100)}%`;
};
const getScoreColor = (score) => {
  if (score >= 0.9) return "#22c55e";
  if (score >= 0.7) return "#3b82f6";
  return "#6b7280";
};
function SourceCitation({
  sources,
  theme,
  maxVisible = 3
}) {
  const [expanded, setExpanded] = reactExports.useState(false);
  const reducedMotion = useReducedMotion();
  if (!sources || sources.length === 0) {
    return null;
  }
  const deduplicatedSources = reactExports.useMemo(() => {
    const sourceMap = /* @__PURE__ */ new Map();
    for (const source of sources) {
      const key = source.filename || source.title;
      const existing = sourceMap.get(key);
      if (!existing || source.relevanceScore > existing.relevanceScore) {
        sourceMap.set(key, source);
      }
    }
    return Array.from(sourceMap.values());
  }, [sources]);
  const visibleSources = expanded ? deduplicatedSources : deduplicatedSources.slice(0, maxVisible);
  const hasMore = deduplicatedSources.length > maxVisible;
  const remainingCount = deduplicatedSources.length - maxVisible;
  const handleSourceClick = (source) => {
    if (source.url) {
      window.open(source.url, "_blank", "noopener,noreferrer");
    }
  };
  const handleToggle = () => {
    setExpanded(!expanded);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      "data-testid": "source-citation",
      className: `source-citation ${reducedMotion ? "source-citation--reduced-motion" : ""}`,
      style: { marginTop: 8 },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "source-citation__header",
            style: {
              fontSize: 11,
              fontWeight: 600,
              color: theme.textColor,
              opacity: 0.7,
              marginBottom: 6,
              textTransform: "uppercase",
              letterSpacing: "0.5px"
            },
            children: "Sources"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "source-citation__list", style: { display: "flex", flexDirection: "column", gap: 4 }, children: visibleSources.map((source, index) => {
          const isClickable = !!source.url;
          return /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              "data-testid": "source-card",
              className: `source-card ${isClickable ? "source-card--clickable" : ""}`,
              onClick: () => handleSourceClick(source),
              disabled: !isClickable,
              style: {
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 8px",
                borderRadius: 6,
                cursor: isClickable ? "pointer" : "default",
                transition: reducedMotion ? "none" : "background-color 150ms ease",
                border: "none",
                background: "transparent",
                width: "100%",
                textAlign: "left"
              },
              "aria-label": `${source.filename || source.title} - ${formatScore(source.relevanceScore)} relevance`,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "span",
                  {
                    className: "source-card__title",
                    style: {
                      flex: 1,
                      fontSize: 12,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      color: theme.textColor
                    },
                    title: source.filename || source.title,
                    children: source.filename || source.title
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "span",
                  {
                    className: "source-card__score",
                    style: {
                      fontSize: 10,
                      padding: "2px 6px",
                      borderRadius: 4,
                      background: getScoreColor(source.relevanceScore),
                      color: "white",
                      flexShrink: 0
                    },
                    children: formatScore(source.relevanceScore)
                  }
                )
              ]
            },
            `${source.documentId}-${index}`
          );
        }) }),
        hasMore && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            "data-testid": "source-toggle",
            className: "source-citation__toggle",
            onClick: handleToggle,
            style: {
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 4,
              width: "100%",
              padding: "6px 8px",
              marginTop: 6,
              border: "none",
              borderRadius: 6,
              background: "transparent",
              color: theme.primaryColor,
              fontSize: 11,
              fontWeight: 500,
              cursor: "pointer",
              transition: reducedMotion ? "none" : "background-color 150ms ease"
            },
            "aria-expanded": expanded,
            "aria-label": expanded ? "Show fewer sources" : `Show ${remainingCount} more sources`,
            children: expanded ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Show less" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "12", height: "12", viewBox: "0 0 24 24", "aria-hidden": "true", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { fill: "currentColor", d: "M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z" }) })
            ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "View ",
                remainingCount,
                " more"
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "12", height: "12", viewBox: "0 0 24 24", "aria-hidden": "true", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { fill: "currentColor", d: "M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" }) })
            ] })
          }
        )
      ]
    }
  );
}
const ThumbsUpIcon = ({ className }) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "svg",
  {
    viewBox: "0 0 24 24",
    className: className || "feedback-button-icon",
    "aria-hidden": "true",
    children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" })
  }
);
const ThumbsDownIcon = ({ className }) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "svg",
  {
    viewBox: "0 0 24 24",
    className: className || "feedback-button-icon",
    "aria-hidden": "true",
    children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" })
  }
);
function FeedbackRating({
  messageId,
  feedbackEnabled = true,
  userRating,
  theme,
  onSubmit
}) {
  const [rating, setRating] = reactExports.useState(userRating || null);
  const [showCommentForm, setShowCommentForm] = reactExports.useState(false);
  const [comment, setComment] = reactExports.useState("");
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [announcement, setAnnouncement] = reactExports.useState("");
  const commentInputRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    setRating(userRating || null);
  }, [userRating]);
  reactExports.useEffect(() => {
    if (showCommentForm && commentInputRef.current) {
      commentInputRef.current.focus();
    }
  }, [showCommentForm]);
  const handleRatingClick = async (newRating) => {
    if (isSubmitting) return;
    if (newRating === "negative" && rating !== "negative") {
      setRating(newRating);
      setShowCommentForm(true);
      return;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(messageId, newRating);
      setRating(newRating);
      setShowCommentForm(false);
      setComment("");
      setAnnouncement(`Feedback submitted: ${newRating === "positive" ? "Helpful" : "Not helpful"}`);
    } catch (error) {
      console.error("Failed to submit feedback:", error);
      setAnnouncement("Failed to submit feedback. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };
  const handleCommentSubmit = async () => {
    if (isSubmitting || !rating) return;
    setIsSubmitting(true);
    try {
      await onSubmit(messageId, rating, comment || void 0);
      setShowCommentForm(false);
      setComment("");
      setAnnouncement("Feedback submitted with comment");
    } catch (error) {
      console.error("Failed to submit feedback:", error);
      setAnnouncement("Failed to submit feedback. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };
  const handleDismissComment = () => {
    setShowCommentForm(false);
    setComment("");
  };
  const handleKeyDown = (e, ratingValue) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleRatingClick(ratingValue);
    }
  };
  if (!feedbackEnabled) {
    return null;
  }
  const isDarkMode = theme.mode === "dark";
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      "data-testid": "feedback-rating",
      role: "group",
      "aria-label": "Rate this response",
      className: `feedback-rating${isDarkMode ? " feedback-rating--dark" : ""}`,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            "data-testid": "feedback-up",
            type: "button",
            role: "button",
            "aria-label": "Rate as helpful",
            "aria-pressed": rating === "positive",
            disabled: isSubmitting,
            onClick: () => handleRatingClick("positive"),
            onKeyDown: (e) => handleKeyDown(e, "positive"),
            className: `feedback-button${rating === "positive" ? " feedback-button--selected" : ""}`,
            style: {
              backgroundColor: rating === "positive" ? theme.primaryColor : "transparent"
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsx(ThumbsUpIcon, {})
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            "data-testid": "feedback-down",
            type: "button",
            role: "button",
            "aria-label": "Rate as not helpful",
            "aria-pressed": rating === "negative",
            disabled: isSubmitting,
            onClick: () => handleRatingClick("negative"),
            onKeyDown: (e) => handleKeyDown(e, "negative"),
            className: `feedback-button${rating === "negative" ? " feedback-button--selected" : ""}`,
            style: {
              backgroundColor: rating === "negative" ? theme.primaryColor : "transparent"
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsx(ThumbsDownIcon, {})
          }
        ),
        showCommentForm && /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            "data-testid": "feedback-comment-form",
            style: {
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              padding: "8px",
              backgroundColor: isDarkMode ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.02)",
              borderRadius: "12px",
              flex: 1,
              maxWidth: "300px"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: `feedback-comment-${messageId}`, style: { fontSize: "12px", color: theme.textColor }, children: "Tell us how we can improve (optional):" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "textarea",
                {
                  ref: commentInputRef,
                  id: `feedback-comment-${messageId}`,
                  "data-testid": "feedback-comment",
                  value: comment,
                  onChange: (e) => setComment(e.target.value.slice(0, 500)),
                  placeholder: "What would have been more helpful?",
                  maxLength: 500,
                  rows: 2,
                  style: {
                    width: "100%",
                    padding: "8px",
                    border: `1px solid ${isDarkMode ? "rgba(255, 255, 255, 0.2)" : "rgba(0, 0, 0, 0.1)"}`,
                    borderRadius: "8px",
                    backgroundColor: isDarkMode ? "rgba(0, 0, 0, 0.2)" : "#fff",
                    color: theme.textColor,
                    fontFamily: theme.fontFamily,
                    fontSize: "14px",
                    resize: "none"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "8px", justifyContent: "flex-end" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleDismissComment,
                    disabled: isSubmitting,
                    style: {
                      padding: "6px 12px",
                      border: "none",
                      borderRadius: "6px",
                      backgroundColor: "transparent",
                      color: theme.textColor,
                      fontSize: "14px",
                      cursor: "pointer",
                      opacity: 0.7
                    },
                    children: "Skip"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleCommentSubmit,
                    disabled: isSubmitting,
                    style: {
                      padding: "6px 12px",
                      border: "none",
                      borderRadius: "6px",
                      backgroundColor: theme.primaryColor,
                      color: "#fff",
                      fontSize: "14px",
                      fontWeight: 500,
                      cursor: "pointer"
                    },
                    children: "Submit"
                  }
                )
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { style: { fontSize: "11px", color: theme.textColor, opacity: 0.6 }, children: [
                comment.length,
                "/500 characters"
              ] })
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { "aria-live": "polite", "aria-atomic": "true", style: { position: "absolute", left: "-9999px" }, children: announcement })
      ]
    }
  );
}
function getBusinessHoursMessage(businessHours) {
  if (!(businessHours == null ? void 0 : businessHours.hours)) return "Contact us";
  const days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const now = /* @__PURE__ */ new Date();
  const today = days[now.getDay()];
  const todayHours = businessHours.hours[today];
  if (!todayHours) return "Contact us";
  const currentTime = now.getHours() * 60 + now.getMinutes();
  const [openH, openM] = todayHours.open.split(":").map(Number);
  const [closeH, closeM] = todayHours.close.split(":").map(Number);
  if (currentTime >= openH * 60 + openM && currentTime < closeH * 60 + closeM) {
    return "Available now";
  }
  for (let i = 1; i <= 7; i++) {
    const nextDay = days[(now.getDay() + i) % 7];
    const nextHours = businessHours.hours[nextDay];
    if (nextHours) {
      return `Available ${nextDay} at ${nextHours.open}`;
    }
  }
  return "Contact us";
}
function ContactCard({
  contactOptions,
  theme,
  conversationId,
  businessHours,
  onContactClick,
  onShowToast
}) {
  const isDarkMode = theme.mode === "dark";
  const reducedMotion = useReducedMotion();
  const isMobile = reactExports.useCallback(() => {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  }, []);
  const handlePhoneClick = async (option) => {
    try {
      if (isMobile()) {
        window.location.href = `tel:${option.value}`;
        logContactInteraction("phone", "call");
      } else {
        await navigator.clipboard.writeText(option.value);
        logContactInteraction("phone", "copy");
        onShowToast == null ? void 0 : onShowToast("Phone number copied to clipboard");
      }
      onContactClick == null ? void 0 : onContactClick(option);
    } catch (error) {
      console.error("[ContactCard] Phone click failed:", error);
    }
  };
  const handleEmailClick = (option) => {
    try {
      const subject = conversationId ? encodeURIComponent(`Support Request - Conversation ${conversationId}`) : encodeURIComponent("Support Request");
      window.location.href = `mailto:${option.value}?subject=${subject}`;
      logContactInteraction("email");
      onContactClick == null ? void 0 : onContactClick(option);
    } catch (error) {
      console.error("[ContactCard] Email click failed:", error);
    }
  };
  const handleCustomClick = (option) => {
    try {
      window.open(option.value, "_blank", "noopener,noreferrer");
      logContactInteraction("custom", option.label);
      onContactClick == null ? void 0 : onContactClick(option);
    } catch (error) {
      console.error("[ContactCard] Custom click failed:", error);
    }
  };
  if (!contactOptions || contactOptions.length === 0) {
    return null;
  }
  const businessHoursMessage = getBusinessHoursMessage(businessHours || null);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { "data-testid": "contact-card", style: { marginTop: 8 }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        style: {
          fontSize: 12,
          color: theme.textColor,
          opacity: 0.7,
          marginBottom: 8,
          fontWeight: 500
        },
        children: businessHoursMessage
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        style: {
          display: "flex",
          flexWrap: "wrap",
          gap: 8
        },
        children: contactOptions.map((option) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            "data-testid": `contact-${option.type}`,
            role: "button",
            "aria-label": option.label,
            onClick: () => {
              if (option.type === "phone") {
                handlePhoneClick(option);
              } else if (option.type === "email") {
                handleEmailClick(option);
              } else {
                handleCustomClick(option);
              }
            },
            style: {
              display: "flex",
              alignItems: "center",
              gap: 8,
              minHeight: "44px",
              padding: "8px 16px",
              border: `1px solid ${isDarkMode ? "rgba(255, 255, 255, 0.2)" : "rgba(0, 0, 0, 0.1)"}`,
              borderRadius: "20px",
              backgroundColor: isDarkMode ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.02)",
              cursor: "pointer",
              transition: reducedMotion ? "none" : "all 150ms ease",
              color: theme.textColor,
              fontSize: 13,
              fontWeight: 500
            },
            children: [
              option.icon && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: option.icon }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: option.label })
            ]
          },
          `${option.type}-${option.value}`
        ))
      }
    )
  ] });
}
function groupMessages(messages) {
  if (messages.length === 0) return [];
  const groups = [];
  for (const message of messages) {
    if (message.sender === "system") {
      groups.push({ id: message.messageId, sender: "system", messages: [message] });
      continue;
    }
    const lastGroup = groups[groups.length - 1];
    if (!lastGroup || lastGroup.sender === "system" || lastGroup.sender !== message.sender) {
      groups.push({ id: message.messageId, sender: message.sender, messages: [message] });
    } else {
      lastGroup.messages.push(message);
    }
  }
  return groups;
}
function isFirstInGroup(_group, index) {
  return index === 0;
}
function isLastInGroup(group, index) {
  return index === group.messages.length - 1;
}
function isSingleMessage(group) {
  return group.messages.length === 1;
}
function getGroupPosition(group, index) {
  if (isSingleMessage(group)) return "single";
  if (isFirstInGroup(group, index)) return "first";
  if (isLastInGroup(group, index)) return "last";
  return "middle";
}
function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = /* @__PURE__ */ new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1e3);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffWeek = Math.floor(diffDay / 7);
  if (isNaN(date.getTime())) return "Invalid date";
  if (diffMs < 0) return "Just now";
  if (diffSec < 60) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  if (diffWeek < 52) return date.toLocaleDateString(void 0, { month: "short", day: "numeric" });
  return date.toLocaleDateString();
}
function formatAbsoluteTime(dateString) {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "Invalid time";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function MessageList({
  messages,
  botName,
  businessName,
  welcomeMessage,
  theme,
  isLoading,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  onQuickRepliesAvailable,
  onSuggestedRepliesAvailable,
  sessionId,
  onFeedbackSubmit
}) {
  const messagesEndRef = reactExports.useRef(null);
  const prevMessageIdsRef = reactExports.useRef(/* @__PURE__ */ new Set());
  const reducedMotion = useReducedMotion();
  const groups = reactExports.useMemo(() => groupMessages(messages), [messages]);
  const getNewMessageIds = reactExports.useCallback(() => {
    const currentIds = new Set(messages.map((m) => m.messageId));
    const newIds = /* @__PURE__ */ new Set();
    currentIds.forEach((id) => {
      if (!prevMessageIdsRef.current.has(id)) {
        newIds.add(id);
      }
    });
    prevMessageIdsRef.current = currentIds;
    return newIds;
  }, [messages]);
  const newMessageIds = getNewMessageIds();
  reactExports.useEffect(() => {
    var _a;
    (_a = messagesEndRef.current) == null ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
  reactExports.useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if ((lastMessage == null ? void 0 : lastMessage.sender) === "bot" && lastMessage.quick_replies) {
      onQuickRepliesAvailable == null ? void 0 : onQuickRepliesAvailable(lastMessage.quick_replies);
    } else if ((lastMessage == null ? void 0 : lastMessage.sender) === "user") {
      onQuickRepliesAvailable == null ? void 0 : onQuickRepliesAvailable([]);
    }
  }, [messages, onQuickRepliesAvailable]);
  reactExports.useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if ((lastMessage == null ? void 0 : lastMessage.sender) === "bot" && lastMessage.suggestedReplies) {
      onSuggestedRepliesAvailable == null ? void 0 : onSuggestedRepliesAvailable(lastMessage.suggestedReplies);
    } else if ((lastMessage == null ? void 0 : lastMessage.sender) === "user") {
      onSuggestedRepliesAvailable == null ? void 0 : onSuggestedRepliesAvailable([]);
    }
  }, [messages, onSuggestedRepliesAvailable]);
  if (messages.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "message-list message-list--empty",
        role: "log",
        "aria-live": "polite",
        style: {
          flex: 1,
          minHeight: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 16,
          textAlign: "center",
          color: theme.textColor,
          opacity: 0.7
        },
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              width: "48",
              height: "48",
              viewBox: "0 0 24 24",
              fill: "none",
              stroke: "currentColor",
              strokeWidth: "1.5",
              strokeLinecap: "round",
              strokeLinejoin: "round",
              "aria-hidden": "true",
              style: { margin: "0 auto 12px", opacity: 0.5 },
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: welcomeMessage ?? "Start a conversation" })
        ] })
      }
    );
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      "data-testid": "message-list",
      className: "message-list",
      role: "log",
      "aria-live": "polite",
      "aria-label": "Chat messages",
      "aria-busy": isLoading ? "true" : "false",
      style: {
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        padding: 16
      },
      children: [
        groups.map((group) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          MessageGroupComponent,
          {
            group,
            botName,
            businessName,
            theme,
            onAddToCart,
            onProductClick,
            onRemoveFromCart,
            onCheckout,
            addingProductId,
            removingItemId,
            isCheckingOut,
            newMessageIds,
            reducedMotion,
            sessionId,
            onFeedbackSubmit
          },
          group.id
        )),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { ref: messagesEndRef })
      ]
    }
  );
}
function MessageGroupComponent({
  group,
  botName,
  businessName,
  theme,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  newMessageIds,
  reducedMotion,
  sessionId,
  onFeedbackSubmit
}) {
  var _a;
  const isUser = group.sender === "user";
  const isSystem = group.sender === "system";
  const showAvatar = !isUser && !isSystem;
  let displayName = botName;
  if (isUser) {
    displayName = ((_a = group.messages[0]) == null ? void 0 : _a.customerName) || "User";
  } else if (group.sender === "merchant") {
    displayName = businessName || "Merchant";
  } else if (group.sender === "bot") {
    displayName = botName;
  }
  if (isSystem) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        "data-testid": "message-group",
        className: "message-group",
        role: "listitem",
        style: { marginBottom: 12 },
        children: group.messages.map((message) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            "data-testid": "message-bubble",
            className: "message-bubble message-bubble--system",
            style: {
              textAlign: "center",
              color: theme.textColor,
              opacity: 0.7,
              fontSize: 12,
              padding: "4px 8px"
            },
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { whiteSpace: "pre-wrap", wordBreak: "break-word" }, children: renderMessageContent(message.content) })
          },
          message.messageId
        ))
      }
    );
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      "data-testid": "message-group",
      className: "message-group",
      role: "listitem",
      style: { marginBottom: 12 },
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: `message-group__row ${isUser ? "message-group__row--user" : ""}`,
          style: {
            display: "flex",
            alignItems: "flex-end",
            gap: 8,
            flexDirection: isUser ? "row-reverse" : "row"
          },
          children: [
            showAvatar && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "message-group__avatar", style: { flexShrink: 0 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
              MessageAvatar,
              {
                sender: group.sender,
                botName,
                theme,
                size: 32
              }
            ) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                className: "message-group__content",
                style: {
                  display: "flex",
                  flexDirection: "column",
                  gap: 4,
                  maxWidth: "75%"
                },
                children: group.messages.map((message, index) => {
                  const position = getGroupPosition(group, index);
                  const isFirst = position === "first" || position === "single";
                  const isLast = position === "last" || position === "single";
                  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      MessageBubbleInGroup,
                      {
                        message,
                        sender: group.sender,
                        position,
                        displayName: isFirst ? displayName : void 0,
                        theme,
                        showRichContent: isLast,
                        onAddToCart,
                        onProductClick,
                        onRemoveFromCart,
                        onCheckout,
                        addingProductId,
                        removingItemId,
                        isCheckingOut,
                        isNew: newMessageIds.has(message.messageId),
                        reducedMotion,
                        sessionId,
                        onFeedbackSubmit
                      }
                    ),
                    isLast && /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        "data-testid": "message-timestamp",
                        className: `message-bubble__timestamp message-bubble__timestamp--${isUser ? "user" : "bot"}`,
                        title: formatAbsoluteTime(message.createdAt),
                        style: {
                          fontSize: 10,
                          color: theme.textColor,
                          opacity: 0.5,
                          marginTop: 2,
                          textAlign: isUser ? "right" : "left",
                          marginRight: isUser ? 4 : 0,
                          marginLeft: isUser ? 0 : 4
                        },
                        children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "data-testid": "relative-time", children: formatRelativeTime(message.createdAt) })
                      }
                    )
                  ] }, message.messageId);
                })
              }
            )
          ]
        }
      )
    }
  );
}
function MessageBubbleInGroup({
  message,
  sender,
  position,
  displayName,
  theme,
  showRichContent,
  onAddToCart,
  onProductClick,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  isNew = false,
  reducedMotion = false,
  sessionId,
  onFeedbackSubmit
}) {
  const isUser = sender === "user";
  const getBorderRadius = () => {
    if (position === "single") return "16px";
    if (position === "first") return isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px";
    if (position === "middle") return "4px";
    if (position === "last") return isUser ? "16px 4px 4px 16px" : "4px 4px 16px 16px";
    return "16px";
  };
  const shouldAnimate = isNew && isUser && !reducedMotion;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", flexDirection: "column", gap: 4 }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        "data-testid": "message-bubble",
        className: `message-bubble message-bubble--${position} message-bubble--${isUser ? "user" : "bot"}`,
        style: {
          padding: "10px 14px",
          borderRadius: getBorderRadius(),
          backgroundColor: isUser ? theme.userBubbleColor : theme.botBubbleColor,
          color: isUser ? "white" : theme.textColor,
          wordBreak: "break-word",
          animationName: shouldAnimate ? "message-send" : "none",
          animationDuration: shouldAnimate ? "200ms" : "0ms",
          animationTimingFunction: "ease-out",
          animationFillMode: "forwards"
        },
        children: [
          displayName && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: "message-bubble__sender",
              style: {
                fontSize: 11,
                fontWeight: 600,
                marginBottom: 4,
                opacity: 0.8
              },
              children: displayName
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: "message-bubble__content",
              style: { whiteSpace: "pre-wrap", wordBreak: "break-word" },
              children: renderMessageContent(message.content)
            }
          )
        ]
      }
    ),
    showRichContent && !isUser && message.products && message.products.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "message-bubble__rich-content",
        style: { maxWidth: "100%", marginTop: 8 },
        children: message.products.length >= 3 ? /* @__PURE__ */ jsxRuntimeExports.jsx(
          ProductCarousel,
          {
            products: message.products,
            theme,
            onAddToCart,
            onProductClick,
            addingProductId
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(
          ProductList,
          {
            products: message.products,
            theme,
            onAddToCart,
            onProductClick,
            addingProductId
          }
        )
      }
    ),
    showRichContent && !isUser && message.cart && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "message-bubble__rich-content",
        style: { maxWidth: "100%", marginTop: 8 },
        children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          CartView,
          {
            cart: message.cart,
            theme,
            onRemoveItem: onRemoveFromCart,
            onCheckout,
            isCheckingOut,
            removingItemId
          }
        )
      }
    ),
    showRichContent && !isUser && message.checkoutUrl && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: 8 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "a",
      {
        href: message.checkoutUrl,
        target: "_blank",
        rel: "noopener noreferrer",
        style: {
          display: "inline-block",
          padding: "8px 16px",
          backgroundColor: theme.primaryColor,
          color: "white",
          textDecoration: "none",
          borderRadius: 8,
          fontWeight: 500,
          fontSize: 13
        },
        children: "Complete Checkout →"
      }
    ) }),
    showRichContent && !isUser && message.sources && message.sources.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "message-bubble__sources", children: /* @__PURE__ */ jsxRuntimeExports.jsx(SourceCitation, { sources: message.sources, theme }) }),
    showRichContent && !isUser && sender === "bot" && onFeedbackSubmit && /* @__PURE__ */ jsxRuntimeExports.jsx(
      FeedbackRating,
      {
        messageId: message.messageId,
        feedbackEnabled: message.feedbackEnabled,
        userRating: message.userRating,
        theme,
        onSubmit: onFeedbackSubmit
      }
    ),
    showRichContent && !isUser && message.contactOptions && message.contactOptions.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(
      ContactCard,
      {
        contactOptions: message.contactOptions,
        theme,
        conversationId: sessionId,
        onContactClick: () => {
        }
      }
    )
  ] });
}
function renderMessageContent(content) {
  const imageRegex = /(📷\s*Image:\s*)?(https?:\/\/[^\s]+?\.(?:jpg|jpeg|png|gif|webp|svg)(?:\?[^\s]*)?)/gi;
  const result = [];
  let lastIndex = 0;
  let match;
  while ((match = imageRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      result.push(content.slice(lastIndex, match.index));
    }
    const fullMatch = match[0];
    const imageUrl = match[2];
    result.push(
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: 8, marginBottom: 8 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        "img",
        {
          src: imageUrl,
          alt: "Product",
          style: {
            maxWidth: "100%",
            borderRadius: 8,
            display: "block"
          },
          loading: "lazy"
        }
      ) }, match.index)
    );
    lastIndex = match.index + fullMatch.length;
  }
  if (lastIndex < content.length) {
    result.push(content.slice(lastIndex));
  }
  return result.length > 0 ? result : content;
}
const VOICE_LANGUAGE_STORAGE_KEY = "widget-voice-language";
function getStoredLanguage() {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(VOICE_LANGUAGE_STORAGE_KEY);
  } catch {
    return null;
  }
}
function setStoredLanguage(language) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(VOICE_LANGUAGE_STORAGE_KEY, language);
  } catch {
  }
}
function useVoiceInput(config = {}) {
  const storedLanguage = reactExports.useMemo(() => getStoredLanguage(), []);
  const mergedConfig = reactExports.useMemo(() => {
    const base = { ...DEFAULT_VOICE_CONFIG, ...config };
    if (!config.language && storedLanguage) {
      base.language = storedLanguage;
    }
    return base;
  }, [config, storedLanguage]);
  const [state, setState] = reactExports.useState({
    isListening: false,
    isProcessing: false,
    error: null,
    interimTranscript: "",
    finalTranscript: ""
  });
  const recognitionRef = reactExports.useRef(null);
  const isSupported = reactExports.useMemo(() => {
    if (typeof window === "undefined") return false;
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }, []);
  const getSpeechRecognition = reactExports.useCallback(() => {
    if (typeof window === "undefined") return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }, []);
  const startListening = reactExports.useCallback(async () => {
    if (!isSupported) {
      setState((prev) => ({
        ...prev,
        error: "Voice input is not supported in this browser. Please use Chrome, Edge, or Safari."
      }));
      return;
    }
    const SpeechRecognitionConstructor = getSpeechRecognition();
    if (!SpeechRecognitionConstructor) {
      setState((prev) => ({
        ...prev,
        error: "Speech recognition is not available."
      }));
      return;
    }
    try {
      const recognition = new SpeechRecognitionConstructor();
      recognition.continuous = mergedConfig.continuous;
      recognition.interimResults = mergedConfig.interimResults;
      recognition.lang = mergedConfig.language;
      recognition.onstart = () => {
        setState((prev) => ({
          ...prev,
          isListening: true,
          isProcessing: false,
          error: null,
          interimTranscript: "",
          finalTranscript: ""
        }));
      };
      recognition.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        setState((prev) => ({
          ...prev,
          interimTranscript,
          finalTranscript: prev.finalTranscript + finalTranscript
        }));
      };
      recognition.onerror = (event) => {
        let errorMessage = "An error occurred during speech recognition.";
        switch (event.error) {
          case "not-allowed":
          case "permission-denied":
            errorMessage = "Microphone permission denied. Please allow microphone access in your browser settings.";
            break;
          case "no-speech":
            errorMessage = "No speech detected. Please try again.";
            break;
          case "network":
            errorMessage = "Network error occurred. Please check your internet connection.";
            break;
          case "audio-capture":
            errorMessage = "No microphone found. Please connect a microphone and try again.";
            break;
          case "aborted":
            errorMessage = "Speech recognition was aborted.";
            break;
          case "service-not-allowed":
            errorMessage = "Speech recognition service is not allowed.";
            break;
          case "language-not-supported":
            errorMessage = `Language "${mergedConfig.language}" is not supported.`;
            break;
        }
        setState((prev) => ({
          ...prev,
          isListening: false,
          isProcessing: false,
          error: errorMessage
        }));
      };
      recognition.onend = () => {
        setState((prev) => ({
          ...prev,
          isListening: false,
          isProcessing: false
        }));
      };
      recognitionRef.current = recognition;
      recognition.start();
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isListening: false,
        isProcessing: false,
        error: "Failed to start speech recognition. Please try again."
      }));
    }
  }, [isSupported, getSpeechRecognition, mergedConfig]);
  const setLanguage = reactExports.useCallback((language) => {
    setStoredLanguage(language);
    if (recognitionRef.current) {
      recognitionRef.current.lang = language;
    }
  }, []);
  const stopListening = reactExports.useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);
  const cancelListening = reactExports.useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      isListening: false,
      isProcessing: false,
      interimTranscript: ""
    }));
  }, []);
  reactExports.useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);
  return {
    state,
    isSupported,
    startListening,
    stopListening,
    cancelListening,
    setLanguage
  };
}
function MicrophoneIcon({ className }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "svg",
    {
      className,
      width: "24",
      height: "24",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M19 10v2a7 7 0 0 1-14 0v-2" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "12", x2: "12", y1: "19", y2: "22" })
      ]
    }
  );
}
function WaveformAnimation() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "waveform-container", children: [1, 2, 3, 4, 5].map((i) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "waveform-bar" }, i)) });
}
function Spinner() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "voice-spinner" });
}
function ErrorIcon({ className }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "svg",
    {
      className,
      width: "24",
      height: "24",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "10" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "12", x2: "12", y1: "8", y2: "12" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "12", x2: "12.01", y1: "16", y2: "16" })
      ]
    }
  );
}
function VoiceInput({
  config,
  onTranscript,
  onInterimTranscript,
  onError,
  disabled = false,
  theme: _theme,
  onLanguageChange
}) {
  const { state, isSupported, startListening, stopListening, cancelListening, setLanguage } = useVoiceInput(config);
  const [showError, setShowError] = reactExports.useState(false);
  const [startTime, setStartTime] = reactExports.useState(null);
  reactExports.useEffect(() => {
    if (onLanguageChange) {
      window.__voiceInputSetLanguage = setLanguage;
    }
  }, [onLanguageChange, setLanguage]);
  reactExports.useEffect(() => {
    if (state.error) {
      setShowError(true);
      onError == null ? void 0 : onError(state.error);
    }
  }, [state.error, onError]);
  reactExports.useEffect(() => {
    onInterimTranscript == null ? void 0 : onInterimTranscript(state.interimTranscript);
  }, [state.interimTranscript, onInterimTranscript]);
  reactExports.useEffect(() => {
    if (state.finalTranscript && !state.isListening) {
      const durationMs = startTime ? Date.now() - startTime : 0;
      trackVoiceInput(durationMs, true);
      onTranscript == null ? void 0 : onTranscript(state.finalTranscript);
      setStartTime(null);
    }
  }, [state.finalTranscript, state.isListening, startTime, onTranscript]);
  const handleToggle = async () => {
    if (state.isListening) {
      stopListening();
    } else {
      setShowError(false);
      setStartTime(Date.now());
      await startListening();
    }
  };
  const handleCancel = () => {
    cancelListening();
  };
  const handleDismissError = () => {
    setShowError(false);
  };
  const getButtonState = () => {
    if (!isSupported) return "unsupported";
    if (state.error) return "error";
    if (state.isProcessing) return "processing";
    if (state.isListening) return "listening";
    return "idle";
  };
  const buttonState = getButtonState();
  const isDisabled = disabled || !isSupported;
  const getAriaLabel = () => {
    if (!isSupported) return "Voice input not supported in this browser";
    if (state.isListening) return "Stop voice input";
    return "Start voice input";
  };
  const handleKeyDown = (e) => {
    if (e.key === "Escape" && state.isListening) {
      e.preventDefault();
      cancelListening();
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "voice-input-container", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        "data-testid": "voice-input-button",
        type: "button",
        role: "button",
        "aria-label": getAriaLabel(),
        "aria-pressed": state.isListening,
        disabled: isDisabled,
        onClick: handleToggle,
        onKeyDown: handleKeyDown,
        className: `voice-input-button ${buttonState}`,
        title: !isSupported ? "Voice input not supported in this browser" : void 0,
        children: [
          buttonState === "listening" && /* @__PURE__ */ jsxRuntimeExports.jsx(WaveformAnimation, {}),
          buttonState === "processing" && /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, {}),
          buttonState === "error" && /* @__PURE__ */ jsxRuntimeExports.jsx(ErrorIcon, {}),
          buttonState === "unsupported" && /* @__PURE__ */ jsxRuntimeExports.jsx(MicrophoneIcon, {}),
          buttonState === "idle" && /* @__PURE__ */ jsxRuntimeExports.jsx(MicrophoneIcon, {})
        ]
      }
    ),
    state.isListening && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        "data-testid": "voice-input-cancel",
        type: "button",
        "aria-label": "Cancel voice input",
        onClick: handleCancel,
        className: "voice-cancel-button",
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "svg",
          {
            width: "16",
            height: "16",
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round",
            strokeLinejoin: "round",
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", x2: "6", y1: "6", y2: "18" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", x2: "18", y1: "6", y2: "18" })
            ]
          }
        )
      }
    ),
    state.interimTranscript && state.isListening && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        "data-testid": "voice-interim-transcript",
        "aria-live": "polite",
        "aria-label": "Interim transcript",
        className: "voice-interim-transcript",
        children: state.interimTranscript
      }
    ),
    showError && state.error && !state.isListening && /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        "data-testid": "voice-error-message",
        role: "alert",
        className: "voice-error-message",
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(ErrorIcon, {}),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: state.error }),
          state.error.toLowerCase().includes("permission") && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              "data-testid": "voice-permission-instructions",
              className: "voice-permission-instructions",
              style: { fontSize: "0.75rem", marginTop: "4px" },
              children: "To enable microphone access, please check your browser settings and allow microphone permissions for this site."
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: handleDismissError,
              "aria-label": "Dismiss error",
              style: {
                marginLeft: "auto",
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px"
              },
              children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  width: "16",
                  height: "16",
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", x2: "6", y1: "6", y2: "18" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", x2: "18", y1: "6", y2: "18" })
                  ]
                }
              )
            }
          )
        ]
      }
    )
  ] });
}
function MessageInput({
  value,
  onChange,
  onSend,
  disabled,
  placeholder,
  inputRef,
  theme,
  themeMode,
  maxLength = 2e3,
  voiceInputConfig,
  showVoiceInput = true
}) {
  const [interimTranscript, setInterimTranscript] = reactExports.useState("");
  const handleSubmit = (event) => {
    event.preventDefault();
    if (value.trim()) {
      trackMessageSend(value.trim().length);
    }
    onSend();
  };
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (value.trim()) {
        trackMessageSend(value.trim().length);
      }
      onSend();
    }
  };
  const handleVoiceTranscript = (transcript) => {
    onChange(transcript);
    setInterimTranscript("");
    if (inputRef && typeof inputRef !== "function" && inputRef.current) {
      inputRef.current.focus();
    }
  };
  const handleInterimTranscript = (transcript) => {
    setInterimTranscript(transcript);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "form",
    {
      className: "message-input",
      onSubmit: handleSubmit,
      style: {
        display: "flex",
        flexDirection: "column",
        padding: 12,
        borderTop: "1px solid #e5e7eb",
        backgroundColor: theme.backgroundColor,
        borderRadius: `0 0 ${theme.borderRadius}px ${theme.borderRadius}px`,
        flexShrink: 0
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("style", { children: `
        .shopbot-message-input::placeholder {
          color: ${theme.textColor};
          opacity: 0.5;
        }
      ` }),
        interimTranscript && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            "data-testid": "voice-interim-transcript",
            "aria-live": "polite",
            style: {
              fontStyle: "italic",
              color: "#6b7280",
              fontSize: 13,
              padding: "4px 0",
              marginBottom: 8
            },
            children: interimTranscript
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [
          showVoiceInput && /* @__PURE__ */ jsxRuntimeExports.jsx(
            VoiceInput,
            {
              config: voiceInputConfig,
              onTranscript: handleVoiceTranscript,
              onInterimTranscript: handleInterimTranscript,
              disabled,
              theme: {
                primaryColor: theme.primaryColor,
                backgroundColor: theme.backgroundColor,
                textColor: theme.textColor
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              ref: inputRef,
              type: "text",
              className: "shopbot-message-input",
              "data-testid": "message-input",
              value,
              onChange: (e) => onChange(e.target.value),
              onKeyDown: handleKeyDown,
              disabled,
              placeholder,
              "aria-label": "Type a message",
              maxLength,
              style: {
                flex: 1,
                padding: "10px 14px",
                border: themeMode === "dark" ? "1px solid rgba(255,255,255,0.2)" : "1px solid rgba(0,0,0,0.2)",
                borderRadius: 20,
                fontSize: theme.fontSize,
                fontFamily: theme.fontFamily,
                outline: "none",
                color: theme.textColor,
                backgroundColor: disabled ? themeMode === "dark" ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" : "transparent"
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "submit",
              "data-testid": "send-message-button",
              disabled: disabled || !value.trim(),
              "aria-label": "Send message",
              style: {
                padding: "10px 16px",
                backgroundColor: disabled || !value.trim() ? "#e5e7eb" : theme.primaryColor,
                color: disabled || !value.trim() ? "#9ca3af" : "white",
                border: "none",
                borderRadius: 20,
                cursor: disabled || !value.trim() ? "not-allowed" : "pointer",
                fontSize: theme.fontSize,
                fontWeight: 500
              },
              children: "Send"
            }
          )
        ] })
      ]
    }
  );
}
function TypingIndicator({ isVisible, botName, theme }) {
  const reducedMotion = useReducedMotion();
  if (!isVisible) return null;
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: "typing-indicator",
      role: "status",
      "aria-live": "polite",
      "aria-label": `${botName} is typing`,
      style: {
        display: "flex",
        alignItems: "center",
        padding: "8px 16px"
      },
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          style: {
            padding: "10px 14px",
            borderRadius: 16,
            backgroundColor: theme.botBubbleColor,
            display: "flex",
            flexDirection: "column",
            gap: 8
          },
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "span",
              {
                style: {
                  fontSize: 11,
                  color: theme.textColor,
                  marginBottom: 2,
                  opacity: 0.8
                },
                children: botName
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                "data-testid": "typing-dots",
                style: {
                  display: "flex",
                  gap: 4,
                  alignItems: "center",
                  padding: "4px 0"
                },
                children: [0, 1, 2].map((i) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    "data-testid": "typing-dot",
                    style: {
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      backgroundColor: theme.primaryColor,
                      animationName: reducedMotion ? "none" : "typing-dot-bounce",
                      animationDuration: reducedMotion ? "0ms" : "1.4s",
                      animationTimingFunction: "ease-in-out",
                      animationIterationCount: "infinite",
                      animationDelay: reducedMotion ? "0ms" : `${i * 150}ms`
                    }
                  },
                  i
                ))
              }
            )
          ]
        }
      )
    }
  );
}
const severityStyles = {
  [ErrorSeverity.INFO]: {
    bg: "#eff6ff",
    border: "#3b82f6",
    icon: "ℹ️"
  },
  [ErrorSeverity.WARNING]: {
    bg: "#fffbeb",
    border: "#f59e0b",
    icon: "⚠️"
  },
  [ErrorSeverity.ERROR]: {
    bg: "#fef2f2",
    border: "#ef4444",
    icon: "❌"
  },
  [ErrorSeverity.CRITICAL]: {
    bg: "#fef2f2",
    border: "#dc2626",
    icon: "🚨"
  }
};
function ErrorToast({
  error,
  onDismiss,
  onRetry,
  actions,
  autoDismiss = true,
  autoDismissDelay = 8e3,
  showProgress = true
}) {
  const [isVisible, setIsVisible] = reactExports.useState(false);
  const [isExiting, setIsExiting] = reactExports.useState(false);
  const [timeLeft, setTimeLeft] = reactExports.useState(autoDismissDelay);
  const [isPaused, setIsPaused] = reactExports.useState(false);
  const timerRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, []);
  reactExports.useEffect(() => {
    if (!autoDismiss || error.dismissed || isPaused) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 100) {
          handleDismiss();
          return 0;
        }
        return prev - 100;
      });
    }, 100);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoDismiss, error.dismissed, isPaused]);
  const handleDismiss = reactExports.useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(error.id);
    }, 300);
  }, [error.id, onDismiss]);
  const handleRetry = reactExports.useCallback(() => {
    if (onRetry) {
      onRetry(error.id);
      handleDismiss();
    }
  }, [error.id, onRetry, handleDismiss]);
  const handleMouseEnter = () => setIsPaused(true);
  const handleMouseLeave = () => setIsPaused(false);
  const styles = severityStyles[error.severity];
  const progress = timeLeft / autoDismissDelay * 100;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      role: "alert",
      "aria-live": "assertive",
      "aria-atomic": "true",
      className: `error-toast ${isVisible && !isExiting ? "error-toast--visible" : ""} ${isExiting ? "error-toast--exiting" : ""}`,
      style: {
        backgroundColor: styles.bg,
        borderLeft: `4px solid ${styles.border}`,
        borderRadius: "8px",
        padding: "12px 16px",
        marginBottom: "8px",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
        transform: isVisible && !isExiting ? "translateX(0)" : "translateX(100%)",
        opacity: isExiting ? 0 : 1,
        transition: "transform 0.3s ease, opacity 0.3s ease",
        position: "relative",
        overflow: "hidden"
      },
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
      children: [
        showProgress && autoDismiss && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "error-toast__progress",
            style: {
              position: "absolute",
              bottom: 0,
              left: 0,
              height: "3px",
              backgroundColor: styles.border,
              width: `${progress}%`,
              transition: "width 0.1s linear"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            className: "error-toast__content",
            style: {
              display: "flex",
              alignItems: "flex-start",
              gap: "12px"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  className: "error-toast__icon",
                  style: {
                    fontSize: "18px",
                    lineHeight: 1,
                    flexShrink: 0
                  },
                  "aria-hidden": "true",
                  children: styles.icon
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "div",
                {
                  className: "error-toast__body",
                  style: {
                    flex: 1,
                    minWidth: 0
                  },
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        className: "error-toast__title",
                        style: {
                          fontWeight: 600,
                          fontSize: "14px",
                          color: "#1f2937",
                          marginBottom: "4px"
                        },
                        children: error.message
                      }
                    ),
                    error.detail && /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        className: "error-toast__detail",
                        style: {
                          fontSize: "13px",
                          color: "#4b5563",
                          marginBottom: error.retryable || (actions == null ? void 0 : actions.length) ? "12px" : 0
                        },
                        children: error.detail
                      }
                    ),
                    (error.retryable || (actions == null ? void 0 : actions.length)) && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                      "div",
                      {
                        className: "error-toast__actions",
                        style: {
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap"
                        },
                        children: [
                          error.retryable && onRetry && /* @__PURE__ */ jsxRuntimeExports.jsx(
                            "button",
                            {
                              type: "button",
                              onClick: handleRetry,
                              className: "error-toast__retry",
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: styles.border,
                                color: "white",
                                border: "none",
                                borderRadius: "6px",
                                cursor: "pointer",
                                transition: "opacity 0.2s"
                              },
                              onMouseEnter: (e) => e.currentTarget.style.opacity = "0.8",
                              onMouseLeave: (e) => e.currentTarget.style.opacity = "1",
                              children: error.retryAction || "Try Again"
                            }
                          ),
                          error.fallbackUrl && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                            "a",
                            {
                              href: error.fallbackUrl,
                              target: "_blank",
                              rel: "noopener noreferrer",
                              className: "error-toast__fallback",
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: "transparent",
                                color: styles.border,
                                border: `1px solid ${styles.border}`,
                                borderRadius: "6px",
                                textDecoration: "none",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px"
                              },
                              children: [
                                "Visit Store",
                                /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "12", height: "12", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: [
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" }),
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "15 3 21 3 21 9" }),
                                  /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "10", y1: "14", x2: "21", y2: "3" })
                                ] })
                              ]
                            }
                          ),
                          actions == null ? void 0 : actions.map((action, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                            "button",
                            {
                              type: "button",
                              onClick: action.handler,
                              className: `error-toast__action ${action.primary ? "error-toast__action--primary" : ""}`,
                              style: {
                                padding: "6px 12px",
                                fontSize: "13px",
                                fontWeight: 500,
                                backgroundColor: action.primary ? styles.border : "transparent",
                                color: action.primary ? "white" : "#4b5563",
                                border: `1px solid ${action.primary ? styles.border : "#d1d5db"}`,
                                borderRadius: "6px",
                                cursor: "pointer",
                                transition: "opacity 0.2s"
                              },
                              onMouseEnter: (e) => e.currentTarget.style.opacity = "0.8",
                              onMouseLeave: (e) => e.currentTarget.style.opacity = "1",
                              children: action.label
                            },
                            index
                          )),
                          error.retryAfter && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                            "span",
                            {
                              className: "error-toast__retry-after",
                              style: {
                                fontSize: "12px",
                                color: "#6b7280",
                                display: "flex",
                                alignItems: "center"
                              },
                              children: [
                                "Retry in ",
                                formatRetryTime(error.retryAfter)
                              ]
                            }
                          )
                        ]
                      }
                    )
                  ]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  type: "button",
                  onClick: handleDismiss,
                  className: "error-toast__dismiss",
                  "aria-label": "Dismiss error",
                  style: {
                    background: "none",
                    border: "none",
                    padding: "4px",
                    cursor: "pointer",
                    color: "#9ca3af",
                    flexShrink: 0,
                    transition: "color 0.2s"
                  },
                  onMouseEnter: (e) => e.currentTarget.style.color = "#4b5563",
                  onMouseLeave: (e) => e.currentTarget.style.color = "#9ca3af",
                  children: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "16", height: "16", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", y1: "6", x2: "6", y2: "18" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", y1: "6", x2: "18", y2: "18" })
                  ] })
                }
              )
            ]
          }
        )
      ]
    }
  );
}
function ProductDetailModal({
  productId,
  sessionId,
  theme,
  isOpen,
  onClose,
  onAddToCart
}) {
  const [product, setProduct] = reactExports.useState(null);
  const [loading, setLoading] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  const [quantity, setQuantity] = reactExports.useState(1);
  const [added, setAdded] = reactExports.useState(false);
  reactExports.useEffect(() => {
    if (!isOpen || !productId) {
      setProduct(null);
      setError(null);
      setQuantity(1);
      setAdded(false);
      return;
    }
    const fetchProduct = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await widgetClient.getProduct(sessionId, productId);
        setProduct(data);
      } catch (err) {
        setError(err instanceof WidgetApiException ? err.message : "Failed to load product");
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [isOpen, productId, sessionId]);
  reactExports.useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);
  reactExports.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);
  if (!isOpen) return null;
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  const inStock = product && product.available && (product.inventoryQuantity ?? 0) > 0;
  const maxQuantity = (product == null ? void 0 : product.inventoryQuantity) ?? 99;
  const handleAddToCartClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!product || !inStock || !onAddToCart) return;
    onAddToCart(product, quantity);
    setAdded(true);
    setTimeout(() => {
      setAdded(false);
      onClose();
    }, 1e3);
  };
  const handleCloseClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onClose();
  };
  const handleIncrement = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity < maxQuantity) {
      setQuantity(quantity + 1);
    }
  };
  const handleDecrement = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };
  const getStockStatus = () => {
    if (!product) return null;
    if (!product.available) {
      return { text: "Out of Stock", color: "#dc2626", bg: "#fef2f2" };
    }
    if (product.inventoryQuantity === 0) {
      return { text: "Out of Stock", color: "#dc2626", bg: "#fef2f2" };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 5) {
      return { text: `Only ${product.inventoryQuantity} in stock`, color: "#ea580c", bg: "#fff7ed" };
    }
    if (product.inventoryQuantity && product.inventoryQuantity <= 10) {
      return { text: `${product.inventoryQuantity} in stock`, color: "#ca8a04", bg: "#fefce8" };
    }
    return { text: "In Stock", color: "#16a34a", bg: "#f0fdf4" };
  };
  const stockStatus = getStockStatus();
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      style: {
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 2147483647,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        backgroundColor: "rgba(0, 0, 0, 0.5)"
      },
      onClick: handleBackdropClick,
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          style: {
            backgroundColor: "#ffffff",
            borderRadius: "16px",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            maxWidth: "400px",
            width: "100%",
            maxHeight: "90vh",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column"
          },
          onClick: (e) => e.stopPropagation(),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                style: {
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "16px",
                  borderBottom: "1px solid #e5e7eb"
                },
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { style: { fontSize: "18px", fontWeight: 600, color: "#111827", margin: 0 }, children: "Product Details" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleCloseClick,
                      style: {
                        padding: "8px",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#9ca3af"
                      },
                      "aria-label": "Close modal",
                      children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M18 6L6 18M6 6l12 12" }) })
                    }
                  )
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { overflowY: "auto", flex: 1 }, children: [
              loading && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", alignItems: "center", justifyContent: "center", padding: "48px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "svg",
                {
                  style: { animation: "spin 1s linear infinite", width: 32, height: 32, color: theme.primaryColor },
                  viewBox: "0 0 24 24",
                  fill: "none",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { style: { opacity: 0.25 }, cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { style: { opacity: 0.75 }, fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })
                  ]
                }
              ) }),
              error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "24px", textAlign: "center" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#dc2626", marginBottom: "16px" }, children: error }),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleCloseClick,
                    style: { padding: "8px 16px", fontSize: "14px", color: "#6b7280", background: "none", border: "none", cursor: "pointer" },
                    children: "Close"
                  }
                )
              ] }),
              product && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "16px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    style: {
                      position: "relative",
                      aspectRatio: "1 / 1",
                      backgroundColor: "#f3f4f6",
                      borderRadius: "8px",
                      overflow: "hidden",
                      marginBottom: "16px"
                    },
                    children: product.imageUrl ? /* @__PURE__ */ jsxRuntimeExports.jsx("img", { src: product.imageUrl, alt: product.title, style: { width: "100%", height: "100%", objectFit: "cover" } }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "64", height: "64", viewBox: "0 0 24 24", fill: "none", stroke: "#9ca3af", strokeWidth: "1.5", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" }) }) })
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { style: { fontSize: "20px", fontWeight: 600, color: "#111827", marginBottom: "8px" }, children: product.title }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "24px", fontWeight: 700, color: theme.primaryColor, marginBottom: "12px" }, children: [
                  "$",
                  product.price.toFixed(2)
                ] }),
                stockStatus && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    style: {
                      display: "inline-flex",
                      alignItems: "center",
                      padding: "4px 12px",
                      borderRadius: "9999px",
                      fontSize: "12px",
                      fontWeight: 500,
                      backgroundColor: stockStatus.bg,
                      color: stockStatus.color,
                      marginBottom: "12px"
                    },
                    children: stockStatus.text
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", flexWrap: "wrap", gap: "16px", marginBottom: "12px", fontSize: "14px" }, children: [
                  product.productType && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { color: "#6b7280" }, children: "Category: " }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontWeight: 500, color: "#111827" }, children: product.productType })
                  ] }),
                  product.vendor && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { color: "#6b7280" }, children: "Vendor: " }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontWeight: 500, color: "#111827" }, children: product.vendor })
                  ] })
                ] }),
                product.description && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { borderTop: "1px solid #e5e7eb", paddingTop: "12px" }, children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { style: { fontSize: "14px", fontWeight: 500, color: "#374151", marginBottom: "8px" }, children: "Description" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "14px", color: "#4b5563", lineHeight: 1.6, whiteSpace: "pre-line" }, children: product.description })
                ] })
              ] })
            ] }),
            product && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "16px", borderTop: "1px solid #e5e7eb", backgroundColor: "#f9fafb" }, children: [
              inStock && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: "14px", color: "#4b5563" }, children: "Qty:" }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", border: "1px solid #d1d5db", borderRadius: "8px" }, children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleDecrement,
                      disabled: quantity <= 1,
                      style: {
                        width: "32px",
                        height: "32px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "none",
                        border: "none",
                        borderRight: "1px solid #d1d5db",
                        cursor: quantity <= 1 ? "not-allowed" : "pointer",
                        fontSize: "16px",
                        fontWeight: 500,
                        color: "#374151",
                        opacity: quantity <= 1 ? 0.5 : 1
                      },
                      children: "-"
                    }
                  ),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { padding: "0 16px", textAlign: "center", minWidth: "40px" }, children: quantity }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: handleIncrement,
                      disabled: quantity >= maxQuantity,
                      style: {
                        width: "32px",
                        height: "32px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "none",
                        border: "none",
                        borderLeft: "1px solid #d1d5db",
                        cursor: quantity >= maxQuantity ? "not-allowed" : "pointer",
                        fontSize: "16px",
                        fontWeight: 500,
                        color: "#374151",
                        opacity: quantity >= maxQuantity ? 0.5 : 1
                      },
                      children: "+"
                    }
                  )
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "8px" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleAddToCartClick,
                    disabled: !inStock || added,
                    style: {
                      flex: 1,
                      padding: "10px 16px",
                      borderRadius: "8px",
                      fontWeight: 500,
                      fontSize: "14px",
                      cursor: added || !inStock ? "not-allowed" : "pointer",
                      border: "none",
                      backgroundColor: added ? "#22c55e" : inStock ? theme.primaryColor : "#d1d5db",
                      color: "white",
                      opacity: added || inStock ? 1 : 0.7
                    },
                    children: added ? "Added to Cart!" : inStock ? "Add to Cart" : "Out of Stock"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "button",
                  {
                    type: "button",
                    onClick: handleCloseClick,
                    style: {
                      padding: "10px 16px",
                      backgroundColor: "#e5e7eb",
                      color: "#374151",
                      borderRadius: "8px",
                      fontWeight: 500,
                      fontSize: "14px",
                      border: "none",
                      cursor: "pointer"
                    },
                    children: "Close"
                  }
                )
              ] })
            ] })
          ]
        }
      )
    }
  );
}
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const mergeClasses = (...classes) => classes.filter((className, index, array) => {
  return Boolean(className) && className.trim() !== "" && array.indexOf(className) === index;
}).join(" ").trim();
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const toKebabCase = (string) => string.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const toCamelCase = (string) => string.replace(
  /^([A-Z])|[\s-_]+(\w)/g,
  (match, p1, p2) => p2 ? p2.toUpperCase() : p1.toLowerCase()
);
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const toPascalCase = (string) => {
  const camelCase = toCamelCase(string);
  return camelCase.charAt(0).toUpperCase() + camelCase.slice(1);
};
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
var defaultAttributes = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round"
};
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const hasA11yProp = (props) => {
  for (const prop in props) {
    if (prop.startsWith("aria-") || prop === "role" || prop === "title") {
      return true;
    }
  }
  return false;
};
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const Icon = reactExports.forwardRef(
  ({
    color = "currentColor",
    size = 24,
    strokeWidth = 2,
    absoluteStrokeWidth,
    className = "",
    children,
    iconNode,
    ...rest
  }, ref) => reactExports.createElement(
    "svg",
    {
      ref,
      ...defaultAttributes,
      width: size,
      height: size,
      stroke: color,
      strokeWidth: absoluteStrokeWidth ? Number(strokeWidth) * 24 / Number(size) : strokeWidth,
      className: mergeClasses("lucide", className),
      ...!children && !hasA11yProp(rest) && { "aria-hidden": "true" },
      ...rest
    },
    [
      ...iconNode.map(([tag, attrs]) => reactExports.createElement(tag, attrs)),
      ...Array.isArray(children) ? children : [children]
    ]
  )
);
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const createLucideIcon = (iconName, iconNode) => {
  const Component = reactExports.forwardRef(
    ({ className, ...props }, ref) => reactExports.createElement(Icon, {
      ref,
      iconNode,
      className: mergeClasses(
        `lucide-${toKebabCase(toPascalCase(iconName))}`,
        `lucide-${iconName}`,
        className
      ),
      ...props
    })
  );
  Component.displayName = toPascalCase(iconName);
  return Component;
};
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const __iconNode$1 = [["path", { d: "M21 12a9 9 0 1 1-6.219-8.56", key: "13zald" }]];
const LoaderCircle = createLucideIcon("loader-circle", __iconNode$1);
/**
 * @license lucide-react v0.563.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */
const __iconNode = [
  ["path", { d: "M12 20h.01", key: "zekei9" }],
  ["path", { d: "M8.5 16.429a5 5 0 0 1 7 0", key: "1bycff" }],
  ["path", { d: "M5 12.859a10 10 0 0 1 5.17-2.69", key: "1dl1wf" }],
  ["path", { d: "M19 12.859a10 10 0 0 0-2.007-1.523", key: "4k23kn" }],
  ["path", { d: "M2 8.82a15 15 0 0 1 4.177-2.643", key: "1grhjp" }],
  ["path", { d: "M22 8.82a15 15 0 0 0-11.288-3.764", key: "z3jwby" }],
  ["path", { d: "m2 2 20 20", key: "1ooewy" }]
];
const WifiOff = createLucideIcon("wifi-off", __iconNode);
const ConnectionStatusIndicator = ({ status }) => {
  if (status === "connected") {
    return null;
  }
  const getStatusConfig = () => {
    switch (status) {
      case "connecting":
        return {
          icon: LoaderCircle,
          text: "Connecting...",
          bgColor: "bg-yellow-50",
          textColor: "text-yellow-700",
          borderColor: "border-yellow-200",
          animate: true
        };
      case "disconnected":
        return {
          icon: WifiOff,
          text: "Disconnected - Reconnecting...",
          bgColor: "bg-orange-50",
          textColor: "text-orange-700",
          borderColor: "border-orange-200",
          animate: false
        };
      case "error":
        return {
          icon: WifiOff,
          text: "Connection error",
          bgColor: "bg-red-50",
          textColor: "text-red-700",
          borderColor: "border-red-200",
          animate: false
        };
      default:
        return null;
    }
  };
  const config = getStatusConfig();
  if (!config) return null;
  const Icon2 = config.icon;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `
        flex items-center gap-2 px-3 py-2 text-sm
        ${config.bgColor} ${config.textColor} border ${config.borderColor}
        rounded-lg
      `,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Icon2,
          {
            size: 14,
            className: config.animate ? "animate-spin" : ""
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: config.text })
      ]
    }
  );
};
const CONSENT_MESSAGES = {
  friendly: {
    title: "Save your preferences?",
    description: "I can remember your preferences to help you shop faster next time! 😊 Your data stays private and you can change this anytime."
  },
  professional: {
    title: "Save conversation data?",
    description: "To provide personalized service in future conversations, I can save your preferences. Your data is handled according to privacy regulations."
  },
  enthusiastic: {
    title: "Remember me?! 🎉",
    description: "Want me to remember your preferences so I can help you shop EVEN FASTER next time?! Your data stays safe and you can always change your mind!"
  }
};
function ConsentPrompt({
  isOpen,
  isLoading,
  isTyping = false,
  promptShown,
  consentGranted,
  theme,
  botName,
  personality = "friendly",
  onConfirmConsent,
  onDismiss
}) {
  const [isProcessing, setIsProcessing] = reactExports.useState(false);
  console.log("[ConsentPrompt] render:", { isOpen, promptShown, consentGranted, shouldRender: isOpen && promptShown && consentGranted === null });
  if (!isOpen || !promptShown || consentGranted !== null) {
    return null;
  }
  const handleConsent = async (consented) => {
    setIsProcessing(true);
    try {
      await onConfirmConsent(consented);
    } finally {
      setIsProcessing(false);
    }
  };
  const handleOptIn = () => handleConsent(true);
  const handleOptOut = () => handleConsent(false);
  const handleDismiss = () => onDismiss == null ? void 0 : onDismiss();
  const disabled = isLoading || isTyping || isProcessing;
  const messages = CONSENT_MESSAGES[personality];
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": "consent-title",
      "aria-describedby": "consent-description",
      className: "shopbot-consent-prompt",
      style: {
        padding: "16px",
        backgroundColor: theme.botBubbleColor,
        borderRadius: theme.borderRadius,
        margin: "8px 0",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)"
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            id: "consent-title",
            style: {
              fontSize: "14px",
              fontWeight: 600,
              marginBottom: "8px",
              color: theme.textColor
            },
            children: messages.title
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "p",
          {
            id: "consent-description",
            style: {
              fontSize: "13px",
              lineHeight: "1.5",
              marginBottom: "12px",
              color: theme.textColor,
              opacity: 0.9
            },
            children: messages.description.replace("{botName}", botName)
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              display: "flex",
              gap: "8px",
              justifyContent: "flex-end"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  type: "button",
                  onClick: handleOptOut,
                  disabled,
                  style: {
                    padding: "8px 16px",
                    fontSize: "13px",
                    fontWeight: 500,
                    border: `1px solid ${theme.primaryColor}`,
                    backgroundColor: "transparent",
                    color: theme.primaryColor,
                    borderRadius: theme.borderRadius / 2,
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.6 : 1,
                    transition: "all 0.2s ease"
                  },
                  "aria-label": "Decline to save preferences",
                  children: "No, don't save"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  type: "button",
                  onClick: handleOptIn,
                  disabled,
                  style: {
                    padding: "8px 16px",
                    fontSize: "13px",
                    fontWeight: 500,
                    border: "none",
                    backgroundColor: theme.primaryColor,
                    color: "white",
                    borderRadius: theme.borderRadius / 2,
                    cursor: disabled ? "not-allowed" : "pointer",
                    opacity: disabled ? 0.6 : 1,
                    transition: "all 0.2s ease"
                  },
                  "aria-label": "Agree to save preferences",
                  children: "Yes, save my preferences"
                }
              )
            ]
          }
        ),
        onDismiss && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            onClick: handleDismiss,
            disabled,
            style: {
              position: "absolute",
              top: "8px",
              right: "8px",
              padding: "4px",
              background: "none",
              border: "none",
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: 0.6,
              fontSize: "16px"
            },
            "aria-label": "Close consent prompt",
            children: "×"
          }
        )
      ]
    }
  );
}
function QuickReplyButton({
  reply,
  index,
  onClick,
  onKeyDown,
  theme,
  disabled,
  isSelected,
  reducedMotion
}) {
  const { ripples, createRipple } = useRipple();
  const handleClick = (e) => {
    if (disabled) return;
    createRipple(e);
    onClick(reply, index);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "button",
    {
      "data-testid": `quick-reply-button-${reply.id}`,
      type: "button",
      role: "button",
      "aria-label": reply.text,
      disabled: disabled || isSelected,
      onClick: handleClick,
      onKeyDown: (e) => onKeyDown(e, reply, index),
      className: `quick-reply-button${reducedMotion ? " quick-reply-button--reduced-motion" : ""}`,
      style: {
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "6px",
        minHeight: "40px",
        padding: "8px 14px",
        border: `1px solid ${theme.primaryColor}33`,
        // 20% opacity border
        borderRadius: "16px",
        backgroundColor: `${theme.primaryColor}1a`,
        // 10% opacity background
        color: theme.primaryColor,
        fontFamily: theme.fontFamily,
        fontSize: "13px",
        fontWeight: 500,
        cursor: disabled || isSelected ? "not-allowed" : "pointer",
        opacity: disabled || isSelected ? 0.5 : 1,
        transition: reducedMotion ? "none" : "all 150ms ease",
        whiteSpace: "nowrap",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)"
      },
      onMouseEnter: (e) => {
        if (!disabled && !isSelected) {
          e.currentTarget.style.backgroundColor = `${theme.primaryColor}26`;
          e.currentTarget.style.borderColor = `${theme.primaryColor}66`;
          e.currentTarget.style.transform = "translateY(-1px)";
        }
      },
      onMouseLeave: (e) => {
        if (!disabled && !isSelected) {
          e.currentTarget.style.backgroundColor = `${theme.primaryColor}1a`;
          e.currentTarget.style.borderColor = `${theme.primaryColor}33`;
          e.currentTarget.style.transform = "translateY(0)";
        }
      },
      children: [
        reply.icon && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { fontSize: "16px" }, "aria-hidden": "true", children: reply.icon }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: reply.text }),
        ripples.map((ripple) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          "span",
          {
            "data-testid": "ripple-effect",
            style: {
              position: "absolute",
              left: ripple.x,
              top: ripple.y,
              width: 10,
              height: 10,
              borderRadius: "50%",
              backgroundColor: "rgba(255, 255, 255, 0.3)",
              transform: "translate(-50%, -50%)",
              pointerEvents: "none",
              animationName: reducedMotion ? "none" : "ripple",
              animationDuration: reducedMotion ? "0ms" : "600ms",
              animationTimingFunction: "ease-out",
              animationFillMode: "forwards"
            }
          },
          ripple.id
        ))
      ]
    },
    reply.id
  );
}
function QuickReplyButtons({
  quickReplies,
  onReply,
  theme,
  dismissOnSelect = true,
  disabled = false
}) {
  const [selectedIndex, setSelectedIndex] = reactExports.useState(null);
  const reducedMotion = useReducedMotion();
  const handleClick = (reply, index) => {
    if (disabled) return;
    setSelectedIndex(index);
    trackQuickReplyClick(reply.text);
    onReply(reply);
  };
  const handleKeyDown = (e, reply, index) => {
    if (disabled) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick(reply, index);
    }
  };
  if (!quickReplies || quickReplies.length === 0) {
    return null;
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      "data-testid": "quick-reply-buttons",
      role: "group",
      "aria-label": "Quick reply options",
      className: "quick-reply-buttons",
      style: {
        display: "flex",
        flexWrap: "wrap",
        gap: "8px",
        padding: "8px 16px",
        flexShrink: 0
      },
      children: quickReplies.map((reply, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        QuickReplyButton,
        {
          reply,
          index,
          onClick: handleClick,
          onKeyDown: handleKeyDown,
          theme,
          disabled,
          isSelected: dismissOnSelect && selectedIndex !== null,
          reducedMotion
        },
        reply.id
      ))
    }
  );
}
function FAQQuickButtonItem({
  button,
  index,
  onClick,
  theme,
  disabled,
  reducedMotion
}) {
  const { ripples, createRipple } = useRipple();
  const handleClick = (e) => {
    if (disabled) return;
    createRipple(e);
    onClick(button, index);
  };
  const handleKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick(button, index);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "button",
    {
      "data-testid": `faq-quick-button-${button.id}`,
      type: "button",
      role: "button",
      "aria-label": button.question,
      tabIndex: 0,
      disabled,
      onClick: handleClick,
      onKeyDown: handleKeyDown,
      className: "faq-quick-button",
      style: {
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "6px",
        minHeight: "40px",
        padding: "8px 14px",
        border: `1px solid ${theme.primaryColor}33`,
        // 20% opacity border
        borderRadius: "16px",
        backgroundColor: `${theme.primaryColor}1a`,
        // 10% opacity background
        color: theme.primaryColor,
        fontFamily: theme.fontFamily,
        fontSize: "13px",
        fontWeight: 500,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: reducedMotion ? "none" : "all 150ms ease",
        whiteSpace: "nowrap",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)"
      },
      onMouseEnter: (e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = `${theme.primaryColor}26`;
          e.currentTarget.style.borderColor = `${theme.primaryColor}66`;
          e.currentTarget.style.transform = "translateY(-1px)";
        }
      },
      onMouseLeave: (e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = `${theme.primaryColor}1a`;
          e.currentTarget.style.borderColor = `${theme.primaryColor}33`;
          e.currentTarget.style.transform = "translateY(0)";
        }
      },
      children: [
        button.icon && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "faq-quick-button-icon", style: { fontSize: "16px" }, "aria-hidden": "true", children: button.icon }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "faq-quick-button-text", children: button.question }),
        ripples.map((ripple) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          "span",
          {
            "data-testid": "ripple-effect",
            style: {
              position: "absolute",
              left: ripple.x,
              top: ripple.y,
              width: 10,
              height: 10,
              borderRadius: "50%",
              backgroundColor: "rgba(255, 255, 255, 0.3)",
              transform: "translate(-50%, -50%)",
              pointerEvents: "none",
              animationName: reducedMotion ? "none" : "ripple",
              animationDuration: reducedMotion ? "0ms" : "600ms",
              animationTimingFunction: "ease-out",
              animationFillMode: "forwards"
            }
          },
          ripple.id
        ))
      ]
    }
  );
}
const FAQQuickButtons = ({
  buttons,
  onButtonClick,
  theme,
  disabled = false
}) => {
  const reducedMotion = useReducedMotion();
  const handleClick = (button, _index) => {
    onButtonClick(button);
  };
  if (!buttons || buttons.length === 0) {
    return null;
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      "data-testid": "faq-quick-buttons",
      role: "group",
      "aria-label": "FAQ quick buttons",
      className: "faq-quick-buttons",
      style: {
        display: "flex",
        flexWrap: "wrap",
        gap: "8px",
        padding: "8px 0"
      },
      children: buttons.map((button, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        FAQQuickButtonItem,
        {
          button,
          index,
          onClick: handleClick,
          theme,
          disabled,
          reducedMotion
        },
        button.id
      ))
    }
  );
};
function SuggestedReplies({
  suggestions,
  onSelect,
  theme,
  disabled = false
}) {
  const [selectedIndex, setSelectedIndex] = reactExports.useState(null);
  const reducedMotion = useReducedMotion();
  const handleClick = (suggestion, index) => {
    if (disabled) return;
    setSelectedIndex(index);
    onSelect(suggestion);
  };
  const handleKeyDown = (e, suggestion, index) => {
    if (disabled) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleClick(suggestion, index);
    }
  };
  if (!suggestions || suggestions.length === 0) {
    return null;
  }
  const limitedSuggestions = suggestions.slice(0, 4);
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      "data-testid": "suggested-replies",
      role: "group",
      "aria-label": "Suggested replies",
      className: "suggested-replies",
      style: {
        display: "flex",
        flexWrap: "nowrap",
        gap: "8px",
        padding: "8px 12px",
        flexShrink: 0,
        overflowX: "auto",
        WebkitOverflowScrolling: "touch"
      },
      children: limitedSuggestions.map((suggestion, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          "data-testid": `suggested-reply-${index}`,
          type: "button",
          role: "button",
          "aria-label": suggestion,
          disabled: disabled || selectedIndex !== null,
          onClick: () => handleClick(suggestion, index),
          onKeyDown: (e) => handleKeyDown(e, suggestion, index),
          className: `suggested-reply-chip${reducedMotion ? " suggested-reply-chip--reduced-motion" : ""}`,
          style: {
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "40px",
            padding: "8px 16px",
            border: `1px solid ${theme.primaryColor}33`,
            borderRadius: "20px",
            backgroundColor: `${theme.primaryColor}1a`,
            color: theme.primaryColor,
            fontFamily: theme.fontFamily,
            fontSize: "13px",
            fontWeight: 500,
            cursor: disabled || selectedIndex !== null ? "not-allowed" : "pointer",
            opacity: disabled || selectedIndex !== null ? 0.5 : 1,
            transition: reducedMotion ? "none" : "all 150ms ease",
            whiteSpace: "nowrap",
            flexShrink: 0,
            boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
            position: "relative"
          },
          onMouseEnter: (e) => {
            if (!disabled && selectedIndex === null) {
              e.currentTarget.style.backgroundColor = `${theme.primaryColor}26`;
              e.currentTarget.style.borderColor = `${theme.primaryColor}66`;
              e.currentTarget.style.transform = "translateY(-1px)";
            }
          },
          onMouseLeave: (e) => {
            if (!disabled && selectedIndex === null) {
              e.currentTarget.style.backgroundColor = `${theme.primaryColor}1a`;
              e.currentTarget.style.borderColor = `${theme.primaryColor}33`;
              e.currentTarget.style.transform = "translateY(0)";
            }
          },
          children: suggestion
        },
        suggestion
      ))
    }
  );
}
function ChatWindow({
  isOpen,
  onClose,
  theme,
  config,
  messages,
  isTyping,
  onSendMessage,
  error,
  errors = [],
  onDismissError,
  onRetryError,
  onAddToCart,
  onRemoveFromCart,
  onCheckout,
  addingProductId,
  removingItemId,
  isCheckingOut,
  sessionId,
  connectionStatus = "disconnected",
  consentState,
  onRecordConsent,
  onClearHistory,
  position = { x: 0, y: 0 },
  isDragging = false,
  isMinimized: _isMinimized = false,
  onDragStart,
  onMinimize,
  themeMode = "auto",
  onThemeToggle,
  faqQuickButtons,
  onFaqButtonClick,
  onFeedbackSubmit
}) {
  var _a, _b, _c, _d;
  const [inputValue, setInputValue] = reactExports.useState("");
  const [selectedProductId, setSelectedProductId] = reactExports.useState(null);
  const [isProductModalOpen, setIsProductModalOpen] = reactExports.useState(false);
  const [showMenu, setShowMenu] = reactExports.useState(false);
  const [activeQuickReplies, setActiveQuickReplies] = reactExports.useState(null);
  const [showFaqButtons, setShowFaqButtons] = reactExports.useState(true);
  const [activeSuggestions, setActiveSuggestions] = reactExports.useState(null);
  const inputRef = reactExports.useRef(null);
  const menuRef = reactExports.useRef(null);
  const handleInputChange = (value) => {
    setInputValue(value);
    if (value.length > 0 && activeSuggestions) {
      setActiveSuggestions(null);
    }
  };
  const handleProductClick = (product) => {
    setSelectedProductId(product.id);
    setIsProductModalOpen(true);
  };
  const handleProductModalClose = () => {
    setIsProductModalOpen(false);
    setSelectedProductId(null);
  };
  const handleProductAddToCart = (product, _quantity) => {
    if (onAddToCart && product.variantId) {
      onAddToCart({
        id: product.id,
        variantId: product.variantId,
        title: product.title,
        description: product.description ?? void 0,
        price: product.price,
        imageUrl: product.imageUrl ?? void 0,
        available: product.available,
        productType: product.productType ?? void 0
      });
    }
  };
  reactExports.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);
  reactExports.useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);
  reactExports.useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };
    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showMenu]);
  const handleClearHistory = async () => {
    if (onClearHistory) {
      setShowMenu(false);
      await onClearHistory();
    }
  };
  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    setInputValue("");
    setActiveSuggestions(null);
    await onSendMessage(message);
  };
  const handleQuickReply = async (reply) => {
    setActiveQuickReplies(null);
    await onSendMessage(reply.payload ?? reply.text);
  };
  const handleQuickRepliesAvailable = (replies) => {
    if (replies && replies.length > 0) {
      setActiveQuickReplies(replies);
    } else {
      setActiveQuickReplies(null);
    }
  };
  const handleSuggestedRepliesAvailable = (suggestions) => {
    if (suggestions && suggestions.length > 0) {
      setActiveSuggestions(suggestions);
    } else {
      setActiveSuggestions(null);
    }
  };
  const handleFaqButtonClick = async (button) => {
    if (onFaqButtonClick) {
      onFaqButtonClick(button);
    } else {
      setShowFaqButtons(false);
      await onSendMessage(button.question);
    }
  };
  const handleSuggestionSelect = async (suggestion) => {
    setActiveSuggestions(null);
    await onSendMessage(suggestion);
  };
  reactExports.useEffect(() => {
    const userMessages = messages.filter((m) => m.sender === "user");
    if (userMessages.length > 0) {
      setShowFaqButtons(false);
    }
  }, [messages]);
  if (!isOpen) return null;
  const isMobile = typeof window !== "undefined" && window.innerWidth < 768;
  const isDefaultPosition = isMobile || !position || position.x === 0 && position.y === 0;
  const windowPosition = position || { x: 0, y: 0 };
  const windowStyle = {
    position: "fixed",
    bottom: isMobile ? 0 : isDefaultPosition ? ((_a = theme.position) == null ? void 0 : _a.startsWith("top")) ? "auto" : 90 : "auto",
    right: isMobile ? 0 : isDefaultPosition ? ((_b = theme.position) == null ? void 0 : _b.endsWith("left")) ? "auto" : 20 : "auto",
    top: isMobile ? "auto" : isDefaultPosition ? ((_c = theme.position) == null ? void 0 : _c.startsWith("top")) ? 20 : "auto" : 0,
    left: isMobile ? "auto" : isDefaultPosition ? ((_d = theme.position) == null ? void 0 : _d.endsWith("left")) ? 20 : "auto" : 0,
    transform: isDefaultPosition ? "none" : `translate(${windowPosition.x}px, ${windowPosition.y}px)`,
    width: isMobile ? "100%" : theme.width,
    height: isMobile ? "100%" : theme.height,
    maxWidth: isMobile ? "100%" : "calc(100vw - 40px)",
    maxHeight: isMobile ? "100%" : "calc(100vh - 40px)",
    backgroundColor: theme.backgroundColor,
    borderRadius: theme.borderRadius,
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.15)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    zIndex: 2147483646,
    fontFamily: theme.fontFamily,
    fontSize: theme.fontSize,
    color: theme.textColor,
    transition: isDragging ? "none" : "transform 0.2s ease-out",
    userSelect: isDragging ? "none" : "auto"
  };
  console.log("[ChatWindow] Rendering with state:", {
    isOpen,
    isMobile,
    isDefaultPosition,
    position,
    windowPosition,
    themeWidth: theme.width,
    viewportWidth: window.innerWidth
  });
  console.log("[ChatWindow] Calculated Style:", {
    bottom: windowStyle.bottom,
    right: windowStyle.right,
    left: windowStyle.left,
    top: windowStyle.top,
    transform: windowStyle.transform,
    width: windowStyle.width
  });
  const handleHeaderMouseDown = (e) => {
    if (e.target.closest("button")) return;
    onDragStart == null ? void 0 : onDragStart(e);
  };
  const handleHeaderTouchStart = (e) => {
    if (e.target.closest("button")) return;
    onDragStart == null ? void 0 : onDragStart(e);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(FocusTrap, { active: isOpen && !isProductModalOpen, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        role: "dialog",
        "aria-modal": "true",
        "aria-label": "Chat window",
        "data-testid": "chat-window",
        className: `shopbot-chat-window draggable-chat-window ${isDragging ? "dragging" : ""} ${isDefaultPosition ? "is-default-position" : ""}`,
        style: windowStyle,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: "chat-header chat-header-drag-handle",
              onMouseDown: handleHeaderMouseDown,
              onTouchStart: handleHeaderTouchStart,
              style: {
                padding: "12px 16px",
                backgroundColor: theme.primaryColor,
                color: "white",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderRadius: `${theme.borderRadius}px ${theme.borderRadius}px 0 0`,
                cursor: isDragging ? "grabbing" : "grab"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", alignItems: "center", gap: "8px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "chat-header-title", style: { fontWeight: 600, pointerEvents: "none" }, children: (config == null ? void 0 : config.botName) ?? "Mantisbot" }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "4px" }, children: [
                  onClearHistory && messages.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { position: "relative" }, ref: menuRef, children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "button",
                      {
                        type: "button",
                        onClick: () => setShowMenu(!showMenu),
                        "aria-label": "Chat options",
                        "aria-haspopup": "true",
                        "aria-expanded": showMenu,
                        style: {
                          background: "rgba(255, 255, 255, 0.2)",
                          border: "none",
                          cursor: "pointer",
                          padding: "8px",
                          color: "white",
                          borderRadius: "4px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center"
                        },
                        children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                          "svg",
                          {
                            width: "18",
                            height: "18",
                            viewBox: "0 0 24 24",
                            fill: "none",
                            stroke: "currentColor",
                            strokeWidth: "2",
                            strokeLinecap: "round",
                            strokeLinejoin: "round",
                            "aria-hidden": "true",
                            children: [
                              /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "12", r: "1" }),
                              /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "5", r: "1" }),
                              /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "12", cy: "19", r: "1" })
                            ]
                          }
                        )
                      }
                    ),
                    showMenu && /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        role: "menu",
                        style: {
                          position: "absolute",
                          top: "100%",
                          right: 0,
                          marginTop: "4px",
                          backgroundColor: "white",
                          borderRadius: "8px",
                          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
                          minWidth: "150px",
                          zIndex: 10,
                          overflow: "hidden"
                        },
                        children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                          "button",
                          {
                            type: "button",
                            role: "menuitem",
                            onClick: handleClearHistory,
                            style: {
                              width: "100%",
                              padding: "10px 14px",
                              textAlign: "left",
                              background: "none",
                              border: "none",
                              cursor: "pointer",
                              fontSize: "14px",
                              color: theme.textColor,
                              display: "flex",
                              alignItems: "center",
                              gap: "8px"
                            },
                            onMouseEnter: (e) => {
                              e.target.style.backgroundColor = "#f3f4f6";
                            },
                            onMouseLeave: (e) => {
                              e.target.style.backgroundColor = "transparent";
                            },
                            children: [
                              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                                "svg",
                                {
                                  width: "16",
                                  height: "16",
                                  viewBox: "0 0 24 24",
                                  fill: "none",
                                  stroke: "currentColor",
                                  strokeWidth: "2",
                                  strokeLinecap: "round",
                                  strokeLinejoin: "round",
                                  "aria-hidden": "true",
                                  children: [
                                    /* @__PURE__ */ jsxRuntimeExports.jsx("polyline", { points: "3 6 5 6 21 6" }),
                                    /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" })
                                  ]
                                }
                              ),
                              "Clear History"
                            ]
                          }
                        )
                      }
                    )
                  ] }),
                  onThemeToggle && /* @__PURE__ */ jsxRuntimeExports.jsx(
                    ThemeToggle,
                    {
                      themeMode,
                      onToggle: onThemeToggle
                    }
                  ),
                  onMinimize && /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: onMinimize,
                      "aria-label": "Minimize chat window",
                      title: "Minimize",
                      style: {
                        background: "rgba(255, 255, 255, 0.2)",
                        border: "none",
                        cursor: "pointer",
                        padding: "8px",
                        color: "white",
                        borderRadius: "4px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "background 0.15s ease"
                      },
                      onMouseEnter: (e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)",
                      onMouseLeave: (e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)",
                      children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                        "svg",
                        {
                          width: "18",
                          height: "18",
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor",
                          strokeWidth: "2.5",
                          strokeLinecap: "round",
                          strokeLinejoin: "round",
                          "aria-hidden": "true",
                          children: /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "5", y1: "12", x2: "19", y2: "12" })
                        }
                      )
                    }
                  ),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "button",
                    {
                      type: "button",
                      onClick: onClose,
                      "aria-label": "Close chat window",
                      title: "Close",
                      style: {
                        background: "rgba(255, 255, 255, 0.2)",
                        border: "none",
                        cursor: "pointer",
                        padding: "8px",
                        color: "white",
                        borderRadius: "4px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "background 0.15s ease"
                      },
                      onMouseEnter: (e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)",
                      onMouseLeave: (e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)",
                      children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
                        "svg",
                        {
                          width: "18",
                          height: "18",
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor",
                          strokeWidth: "2.5",
                          strokeLinecap: "round",
                          strokeLinejoin: "round",
                          "aria-hidden": "true",
                          children: [
                            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "18", y1: "6", x2: "6", y2: "18" }),
                            /* @__PURE__ */ jsxRuntimeExports.jsx("line", { x1: "6", y1: "6", x2: "18", y2: "18" })
                          ]
                        }
                      )
                    }
                  )
                ] })
              ]
            }
          ),
          connectionStatus !== "connected" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { padding: "8px 12px", flexShrink: 0 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(ConnectionStatusIndicator, { status: connectionStatus }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            MessageList,
            {
              messages,
              botName: (config == null ? void 0 : config.botName) ?? "Mantisbot",
              businessName: config == null ? void 0 : config.businessName,
              welcomeMessage: config == null ? void 0 : config.welcomeMessage,
              theme,
              isLoading: isTyping,
              onAddToCart,
              onProductClick: handleProductClick,
              onRemoveFromCart,
              onCheckout,
              addingProductId,
              removingItemId,
              isCheckingOut,
              onQuickRepliesAvailable: handleQuickRepliesAvailable,
              onSuggestedRepliesAvailable: handleSuggestedRepliesAvailable,
              sessionId,
              onFeedbackSubmit
            }
          ),
          activeSuggestions && activeSuggestions.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flexShrink: 0, padding: "0 12px 8px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            SuggestedReplies,
            {
              suggestions: activeSuggestions,
              onSelect: handleSuggestionSelect,
              theme,
              disabled: isTyping
            }
          ) }),
          activeQuickReplies && activeQuickReplies.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flexShrink: 0, padding: "0 12px 8px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            QuickReplyButtons,
            {
              quickReplies: activeQuickReplies,
              onReply: handleQuickReply,
              theme,
              dismissOnSelect: true
            }
          ) }),
          showFaqButtons && faqQuickButtons && faqQuickButtons.length > 0 && (config == null ? void 0 : config.onboardingMode) === "general" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flexShrink: 0, padding: "0 12px 8px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            FAQQuickButtons,
            {
              buttons: faqQuickButtons,
              onButtonClick: handleFaqButtonClick,
              theme,
              disabled: isTyping
            }
          ) }),
          consentState && onRecordConsent && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { padding: "8px 12px", flexShrink: 0 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            ConsentPrompt,
            {
              isOpen,
              isLoading: false,
              isTyping,
              promptShown: consentState.promptShown,
              consentGranted: consentState.status === "opted_in" ? true : consentState.status === "opted_out" ? false : null,
              theme,
              botName: (config == null ? void 0 : config.botName) ?? "Mantisbot",
              personality: config == null ? void 0 : config.personality,
              onConfirmConsent: onRecordConsent
            }
          ) }),
          isTyping && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { flexShrink: 0 }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            TypingIndicator,
            {
              isVisible: isTyping,
              botName: (config == null ? void 0 : config.botName) ?? "Mantisbot",
              theme
            }
          ) }),
          (errors.length > 0 || error) && /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: "chat-errors",
              style: {
                padding: "8px",
                maxHeight: "150px",
                overflowY: "auto",
                flexShrink: 0
              },
              children: [
                errors.filter((e) => !e.dismissed).map((widgetError) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  ErrorToast,
                  {
                    error: widgetError,
                    onDismiss: onDismissError || (() => {
                    }),
                    onRetry: onRetryError,
                    autoDismiss: true,
                    autoDismissDelay: 1e4,
                    showProgress: true
                  },
                  widgetError.id
                )),
                error && errors.filter((e) => !e.dismissed).length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(
                  "div",
                  {
                    className: "chat-error",
                    role: "alert",
                    style: {
                      padding: "12px 16px",
                      backgroundColor: "#fee2e2",
                      color: "#dc2626",
                      fontSize: "13px",
                      borderRadius: "8px",
                      borderLeft: "4px solid #dc2626",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "12px"
                    },
                    children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { "aria-hidden": "true", children: "❌" }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: error })
                    ]
                  }
                )
              ]
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            MessageInput,
            {
              value: inputValue,
              onChange: handleInputChange,
              onSend: handleSend,
              disabled: isTyping,
              placeholder: "Type a message...",
              inputRef,
              theme,
              themeMode
            }
          )
        ]
      }
    ) }),
    sessionId && /* @__PURE__ */ jsxRuntimeExports.jsx(
      ProductDetailModal,
      {
        productId: selectedProductId,
        sessionId,
        theme,
        isOpen: isProductModalOpen,
        onClose: handleProductModalClose,
        onAddToCart: handleProductAddToCart
      }
    )
  ] });
}
export {
  ChatWindow as default
};
