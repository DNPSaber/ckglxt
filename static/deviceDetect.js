/**
 * 设备检测工具
 * 用于检测用户设备类型（手机/平板/电脑）
 */

// 检测设备类型并存储到localStorage
function detectDevice() {
    let isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    let isTablet = /iPad|tablet|Nexus 7|Nexus 10/i.test(navigator.userAgent) || 
                   (window.innerWidth >= 768 && window.innerWidth <= 1024);
    
    let deviceType = "desktop"; // 默认为桌面设备
    
    if (isMobile) {
        deviceType = "mobile";
        // 进一步检测是否为平板
        if (isTablet || (window.innerWidth >= 768 && window.innerWidth <= 1024)) {
            deviceType = "tablet";
        }
    }
    
    // 存储到localStorage以便在不同页面使用
    localStorage.setItem('deviceType', deviceType);
    console.log("检测到设备类型:", deviceType);
    return deviceType;
}

// 页面加载时检测设备
window.addEventListener('DOMContentLoaded', function() {
    detectDevice();
});

// 窗口大小改变时重新检测设备
window.addEventListener('resize', function() {
    detectDevice();
});

// 导出函数供其他模块使用
window.getDeviceType = function() {
    // 如果localStorage中没有，则重新检测
    return localStorage.getItem('deviceType') || detectDevice();
};
