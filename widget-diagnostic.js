// Widget Diagnostic Script
// Run this in your browser console on the page where widget should appear

console.log('🔍 WIDGET DIAGNOSTIC TOOL');
console.log('====================');

// 1. Check if ShopBotConfig exists
if (window.ShopBotConfig) {
    console.log('✅ ShopBotConfig found:', window.ShopBotConfig);
    console.log('   Merchant ID:', window.ShopBotConfig.merchantId);
    console.log('   API Base URL:', window.ShopBotConfig.apiBaseUrl);
} else {
    console.error('❌ ShopBotConfig NOT found!');
    console.log('   → Make sure you have window.ShopBotConfig set BEFORE loading widget scripts');
}

// 2. Check React availability
if (window.React) {
    console.log('✅ React loaded:', window.React.version);
} else {
    console.error('❌ React NOT loaded!');
    console.log('   → Add React script before widget script');
}

if (window.ReactDOM) {
    console.log('✅ ReactDOM loaded');
} else {
    console.error('❌ ReactDOM NOT loaded!');
    console.log('   → Add ReactDOM script before widget script');
}

// 3. Check if ShopBotWidget loaded
if (window.ShopBotWidget) {
    console.log('✅ ShopBotWidget loaded');
    console.log('   Available methods:', Object.keys(window.ShopBotWidget));
} else {
    console.error('❌ ShopBotWidget NOT loaded!');
    console.log('   → Check widget.umd.js script is loading');
}

// 4. Look for widget elements
setTimeout(() => {
    console.log('\n🔍 Searching for widget elements...');

    const allElements = document.querySelectorAll('*');
    const widgetElements = [];

    allElements.forEach(el => {
        const className = el.className || '';
        const id = el.id || '';

        if (className.includes('shopbot') ||
            className.includes('chat') ||
            id.includes('shopbot') ||
            id.includes('widget')) {
            widgetElements.push({
                tag: el.tagName,
                class: className,
                id: id,
                visible: el.offsetParent !== null
            });
        }
    });

    if (widgetElements.length > 0) {
        console.log(`✅ Found ${widgetElements.length} potential widget elements:`);
        widgetElements.forEach(el => {
            console.log(`   - ${el.tag}#${el.id} (${el.class}) - ${el.visible ? 'VISIBLE' : 'HIDDEN'}`);
        });
    } else {
        console.error('❌ No widget elements found on page!');
        console.log('   → Widget script may not have initialized');
    }
}, 2000);

// 5. Check for network errors
setTimeout(() => {
    console.log('\n🌐 Checking for network issues...');

    // Try to ping the backend
    fetch('http://localhost:8000/api/v1/widget/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ merchant_id: '1' })
    })
    .then(response => {
        if (response.ok) {
            console.log('✅ Backend API responding correctly');
            return response.json();
        } else {
            console.error('❌ Backend API error:', response.status);
            throw new Error('API error');
        }
    })
    .then(data => {
        console.log('✅ Widget session created successfully');
        console.log('   Session ID:', data.sessionId || data.session_id);
    })
    .catch(error => {
        console.error('❌ Cannot connect to backend:', error.message);
        console.log('   → Check if backend is running on port 8000');
        console.log('   → Check if zrok tunnel is running');
    });
}, 500);

console.log('\n⚠️  Copy this entire output and share it with the developer');
