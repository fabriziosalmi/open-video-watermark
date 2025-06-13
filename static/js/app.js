// Open Video Watermark - Frontend JavaScript
class VideoWatermarkApp {
    constructor() {
        this.socket = null;
        this.processingTasks = new Map();
        this.init();
    }

    init() {
        this.initializeSocket();
        this.setupEventListeners();
        this.loadFiles();
        
        // Theme toggle functionality
        this.initializeTheme();
        
        // Tooltips
        this.initializeTooltips();
        
        // Welcome tour
        this.initializeWelcomeTour();
        
        // Character counter for watermark input
        this.initializeCharacterCounter();
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        this.socket.on('processing_update', (data) => {
            console.log('Processing update received:', data);
            this.updateProcessingStatus(data);
        });
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // File upload form
        const uploadForm = document.getElementById('upload-form');
        uploadForm.addEventListener('submit', (e) => this.handleUpload(e));

        // File input handling
        const fileInput = document.getElementById('files');
        const fileInputDisplay = document.querySelector('.file-input-display');
        
        fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        fileInputDisplay.addEventListener('click', () => fileInput.click());
        
        // Drag and drop
        fileInputDisplay.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileInputDisplay.style.borderColor = 'var(--primary-color)';
            fileInputDisplay.style.background = 'rgba(37, 99, 235, 0.05)';
        });
        
        fileInputDisplay.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileInputDisplay.style.borderColor = 'var(--border-color)';
            fileInputDisplay.style.background = '';
        });
        
        fileInputDisplay.addEventListener('drop', (e) => {
            e.preventDefault();
            fileInputDisplay.style.borderColor = 'var(--border-color)';
            fileInputDisplay.style.background = '';
            
            const files = Array.from(e.dataTransfer.files);
            const videoFiles = files.filter(file => file.type.startsWith('video/'));
            
            if (videoFiles.length > 0) {
                fileInput.files = this.createFileList(videoFiles);
                this.handleFileSelection({ target: { files: videoFiles } });
                
                this.showToast('success', 'Files Added', `${videoFiles.length} video file(s) added successfully`);
            } else {
                this.showToast('warning', 'Invalid Files', 'Please drop video files only');
            }
        });

        // Watermark text preview
        const watermarkInput = document.getElementById('watermark-text');
        const previewText = document.getElementById('preview-text');
        
        if (watermarkInput && previewText) {
            watermarkInput.addEventListener('input', (e) => {
                const text = e.target.value.trim();
                previewText.textContent = text || 'Your watermark will appear here';
                previewText.className = text ? 'preview-text active' : 'preview-text';
            });
        }

        // Strength slider
        const strengthSlider = document.getElementById('strength');
        const strengthValue = document.querySelector('.strength-value');
        const indicators = document.querySelectorAll('.indicator-dot');
        
        strengthSlider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            strengthValue.textContent = value.toFixed(2);
            
            // Update indicator highlights
            indicators.forEach(dot => dot.style.opacity = '0.3');
            
            if (value <= 0.1) {
                indicators[0].style.opacity = '1';
            } else if (value <= 0.2) {
                indicators[1].style.opacity = '1';
            } else {
                indicators[2].style.opacity = '1';
            }
        });
        
        // Refresh files button
        document.getElementById('refresh-files').addEventListener('click', () => {
            this.loadFiles();
        });

        // Processing options toggle
        const toggleButton = document.getElementById('toggle-processing-options');
        const optionsContent = document.getElementById('processing-options-content');
        
        if (toggleButton && optionsContent) {
            toggleButton.addEventListener('click', () => this.toggleProcessingOptions());
        }

        // Update processing options toggle text based on state
        this.updateToggleButtonText();
    }

    createFileList(files) {
        const dt = new DataTransfer();
        files.forEach(file => dt.items.add(file));
        return dt.files;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load files if switching to manage tab
        if (tabName === 'manage') {
            this.loadFiles();
        }
    }

    handleFileSelection(event) {
        const files = Array.from(event.target.files);
        const fileList = document.getElementById('file-list');
        
        // Remove existing analysis
        const existingAnalysis = document.querySelector('.video-analysis');
        if (existingAnalysis) {
            existingAnalysis.remove();
        }
        
        fileList.innerHTML = '';
        
        if (files.length === 0) return;
        
        // Show video analysis
        this.showVideoAnalysis(files);
        
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item enhanced';
            
            // Get video metadata
            const videoElement = document.createElement('video');
            videoElement.preload = 'metadata';
            
            videoElement.addEventListener('loadedmetadata', () => {
                const duration = this.formatDuration(videoElement.duration);
                const resolution = `${videoElement.videoWidth}x${videoElement.videoHeight}`;
                
                fileItem.querySelector('.file-metadata').innerHTML = `
                    <span class="metadata-item">
                        <i class="fas fa-clock"></i> ${duration}
                    </span>
                    <span class="metadata-item">
                        <i class="fas fa-expand-arrows-alt"></i> ${resolution}
                    </span>
                    <span class="metadata-item">
                        <i class="fas fa-hdd"></i> ${this.formatFileSize(file.size)}
                    </span>
                `;
            });
            
            videoElement.src = URL.createObjectURL(file);
            
            fileItem.innerHTML = `
                <div class="file-preview">
                    <video class="video-thumbnail" muted>
                        <source src="${videoElement.src}" type="${file.type}">
                    </video>
                    <div class="file-type-badge">
                        <i class="fas fa-video"></i>
                    </div>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-metadata">
                        <span class="metadata-loading">
                            <i class="fas fa-spinner fa-spin"></i> Loading metadata...
                        </span>
                    </div>
                </div>
                <button type="button" class="remove-file-btn" onclick="app.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            fileList.appendChild(fileItem);
        });
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    removeFile(index) {
        const fileInput = document.getElementById('files');
        const files = Array.from(fileInput.files);
        files.splice(index, 1);
        
        const dt = new DataTransfer();
        files.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        
        this.handleFileSelection({ target: { files: files } });
    }

    async handleUpload(event) {
        event.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('files');
        const watermarkText = document.getElementById('watermark-text').value;
        const strength = document.getElementById('strength').value;
        
        if (fileInput.files.length === 0) {
            this.showToast('error', 'No Files', 'Please select at least one video file.');
            return;
        }
        
        if (!watermarkText.trim()) {
            this.showToast('error', 'Missing Watermark', 'Please enter watermark text.');
            return;
        }
        
        // Add files to form data
        Array.from(fileInput.files).forEach(file => {
            formData.append('files', file);
        });
        formData.append('watermark_text', watermarkText);
        formData.append('strength', strength);
        
        // Add processing options
        const processingOptions = this.getProcessingOptions();
        Object.keys(processingOptions).forEach(key => {
            formData.append(key, processingOptions[key]);
        });
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast('success', 'Upload Successful', result.message);
                
                // Clear form
                fileInput.value = '';
                document.getElementById('file-list').innerHTML = '';
                
                // Show processing status
                this.showProcessingStatus(result.files);
                
                // Join socket rooms for each task
                result.files.forEach(file => {
                    console.log('Joining room for task:', file.task_id);
                    this.socket.emit('join_task', { task_id: file.task_id });
                });
                
            } else {
                this.showToast('error', 'Upload Failed', result.error || 'Unknown error occurred.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('error', 'Upload Failed', 'Network error occurred.');
        }
    }

    showProcessingStatus(files) {
        console.log('Showing processing status for files:', files);
        const processingContainer = document.getElementById('processing-status');
        const processingList = document.getElementById('processing-list');
        
        processingContainer.style.display = 'block';
        
        files.forEach(file => {
            console.log('Adding processing item for:', file);
            const processingItem = document.createElement('div');
            processingItem.className = 'processing-item';
            processingItem.id = `processing-${file.task_id}`;
            
            processingItem.innerHTML = `
                <div class="processing-header">
                    <div class="processing-filename">${file.filename}</div>
                    <div class="processing-status status-queued">Queued</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-message">Waiting to start...</div>
            `;
            
            processingList.appendChild(processingItem);
            this.processingTasks.set(file.task_id, file.filename);
        });
        console.log('Current processing tasks:', this.processingTasks);
    }

    updateProcessingStatus(data) {
        // Use the task_id from the data
        const taskId = data.task_id;
        if (!taskId) {
            console.log('No task_id in processing update:', data);
            return;
        }
        
        const processingItem = document.getElementById(`processing-${taskId}`);
        if (!processingItem) {
            console.log('Could not find processing item for task:', taskId);
            return;
        }
        
        const statusElement = processingItem.querySelector('.processing-status');
        const progressFill = processingItem.querySelector('.progress-fill');
        const progressMessage = processingItem.querySelector('.progress-message');
        
        // Update status
        statusElement.className = `processing-status status-${data.status}`;
        statusElement.textContent = this.getStatusText(data.status);
        
        // Update progress
        progressFill.style.width = `${data.progress}%`;
        progressFill.className = `progress-fill ${data.status}`;
        
        // Update message
        progressMessage.textContent = data.message || '';
        
        // Show completion notification
        if (data.status === 'completed') {
            this.showToast('success', 'Processing Complete', 
                `Successfully watermarked: ${this.processingTasks.get(taskId)}`);
            
            // Remove from processing tasks after delay
            setTimeout(() => {
                this.processingTasks.delete(taskId);
                if (this.processingTasks.size === 0) {
                    document.getElementById('processing-status').style.display = 'none';
                }
            }, 5000);
            
        } else if (data.status === 'error') {
            this.showToast('error', 'Processing Failed', 
                `Failed to process: ${this.processingTasks.get(taskId)}`);
        }
    }

    getStatusText(status) {
        const statusMap = {
            'queued': 'Queued',
            'processing': 'Processing',
            'completed': 'Completed',
            'error': 'Error'
        };
        return statusMap[status] || status;
    }

    async loadFiles() {
        const filesContainer = document.getElementById('files-list');
        filesContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i>Loading files...</div>';
        
        try {
            const response = await fetch('/files');
            const files = await response.json();
            
            if (files.length === 0) {
                filesContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-folder-open"></i>
                        <p>No processed files yet</p>
                        <small>Upload and process some videos to see them here</small>
                    </div>
                `;
                return;
            }
            
            filesContainer.innerHTML = '<div class="files-grid"></div>';
            const filesGrid = filesContainer.querySelector('.files-grid');
            
            files.forEach(file => {
                const fileCard = document.createElement('div');
                fileCard.className = 'file-card';
                
                const processedDate = new Date(file.processed_date).toLocaleString();
                const fileSize = this.formatFileSize(file.file_size);
                
                fileCard.innerHTML = `
                    <div class="file-card-header">
                        <div class="file-info">
                            <div class="file-name">
                                <i class="fas fa-video"></i>
                                ${file.original_filename}
                            </div>
                            <div class="file-meta">Processed: ${processedDate}</div>
                            <div class="file-meta">Size: ${fileSize}</div>
                        </div>
                        <div class="file-actions">
                            <button class="btn btn-success btn-sm" onclick="app.downloadFile('${file.id}')">
                                <i class="fas fa-download"></i> Download
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="app.deleteFile('${file.id}')">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                `;
                
                filesGrid.appendChild(fileCard);
            });
            
        } catch (error) {
            console.error('Error loading files:', error);
            filesContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading files</p>
                    <small>Please try refreshing the page</small>
                </div>
            `;
        }
    }

    downloadFile(fileId) {
        window.open(`/download/${fileId}`, '_blank');
    }

    async deleteFile(fileId) {
        if (!confirm('Are you sure you want to delete this file?')) {
            return;
        }
        
        try {
            const response = await fetch(`/delete/${fileId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showToast('success', 'File Deleted', result.message);
                this.loadFiles(); // Reload files list
            } else {
                this.showToast('error', 'Delete Failed', result.error || 'Unknown error occurred.');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showToast('error', 'Delete Failed', 'Network error occurred.');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showToast(type, title, message) {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type] || icons.info}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto-remove toast after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.3s ease forwards';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toastContainer.removeChild(toast);
                    }
                }, 300);
            }
        }, 5000);
    }

    async getVideoInfo(file) {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            
            video.addEventListener('loadedmetadata', () => {
                const info = {
                    duration: video.duration,
                    width: video.videoWidth,
                    height: video.videoHeight,
                    aspectRatio: (video.videoWidth / video.videoHeight).toFixed(2),
                    size: file.size,
                    type: file.type,
                    name: file.name
                };
                URL.revokeObjectURL(video.src);
                resolve(info);
            });
            
            video.addEventListener('error', () => {
                resolve(null);
            });
            
            video.src = URL.createObjectURL(file);
        });
    }

    async showVideoAnalysis(files) {
        const analysisContainer = document.createElement('div');
        analysisContainer.className = 'video-analysis';
        analysisContainer.innerHTML = `
            <div class="analysis-header">
                <h3><i class="fas fa-chart-bar"></i> Video Analysis</h3>
            </div>
            <div class="analysis-content" id="analysis-content">
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i> Analyzing videos...
                </div>
            </div>
        `;
        
        const uploadForm = document.getElementById('upload-form');
        uploadForm.parentNode.insertBefore(analysisContainer, uploadForm.nextSibling);
        
        const analysisContent = document.getElementById('analysis-content');
        const videoInfos = await Promise.all(files.map(file => this.getVideoInfo(file)));
        
        const totalSize = videoInfos.reduce((sum, info) => sum + (info?.size || 0), 0);
        const totalDuration = videoInfos.reduce((sum, info) => sum + (info?.duration || 0), 0);
        
        analysisContent.innerHTML = `
            <div class="analysis-stats">
                <div class="stat-item">
                    <div class="stat-value">${files.length}</div>
                    <div class="stat-label">Files</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${this.formatFileSize(totalSize)}</div>
                    <div class="stat-label">Total Size</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${this.formatDuration(totalDuration)}</div>
                    <div class="stat-label">Total Duration</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.ceil(totalDuration / 60 * 2)}</div>
                    <div class="stat-label">Est. Processing (min)</div>
                </div>
            </div>
        `;
    }

    toggleProcessingOptions() {
        const toggleButton = document.getElementById('toggle-processing-options');
        const optionsContent = document.getElementById('processing-options-content');
        const toggleText = toggleButton.querySelector('.toggle-text');
        const chevron = toggleButton.querySelector('.fa-chevron-down');
        
        if (optionsContent.classList.contains('expanded')) {
            // Collapse
            optionsContent.classList.remove('expanded');
            toggleButton.classList.remove('active');
            toggleText.textContent = 'Show Advanced Options';
            chevron.style.transform = 'rotate(0deg)';
        } else {
            // Expand
            optionsContent.classList.add('expanded');
            toggleButton.classList.add('active');
            toggleText.textContent = 'Hide Advanced Options';
            chevron.style.transform = 'rotate(180deg)';
        }
    }

    updateToggleButtonText() {
        const toggleButton = document.getElementById('toggle-processing-options');
        const optionsContent = document.getElementById('processing-options-content');
        
        if (toggleButton && optionsContent) {
            const isExpanded = optionsContent.classList.contains('expanded');
            const toggleText = toggleButton.querySelector('.toggle-text');
            
            if (isExpanded) {
                toggleText.textContent = 'Hide Advanced Options';
                toggleButton.classList.add('active');
            } else {
                toggleText.textContent = 'Show Advanced Options';
                toggleButton.classList.remove('active');
            }
        }
    }

    // Enhanced form data collection including processing options
    getProcessingOptions() {
        return {
            preserveQuality: document.getElementById('preserve-quality')?.checked || false,
            optimizeSize: document.getElementById('optimize-size')?.checked || false,
            batchProcessing: document.getElementById('batch-processing')?.checked || false,
            backgroundProcessing: document.getElementById('background-processing')?.checked || false,
            autoDelete: document.getElementById('auto-delete')?.checked || true,
            generatePreview: document.getElementById('generate-preview')?.checked || false,
            outputFormat: document.getElementById('output-format')?.value || 'same',
            compressionLevel: document.getElementById('compression-level')?.value || 'medium'
        };
    }

    // Theme Management
    initializeTheme() {
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        
        // Get saved theme or use system preference
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
        
        this.setTheme(initialTheme);
        
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
    
    setTheme(theme) {
        const themeIcon = document.getElementById('theme-icon');
        document.documentElement.setAttribute('data-theme', theme);
        
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        localStorage.setItem('theme', theme);
    }
    
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    // Tooltip System
    initializeTooltips() {
        const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
        const tooltip = document.getElementById('tooltip');
        
        if (!tooltip) return;
        
        tooltipTriggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', (e) => this.showTooltip(e, tooltip));
            trigger.addEventListener('mouseleave', () => this.hideTooltip(tooltip));
            trigger.addEventListener('mousemove', (e) => this.updateTooltipPosition(e, tooltip));
        });
        
        // Also handle tooltip triggers
        const tooltipTriggerElements = document.querySelectorAll('.tooltip-trigger');
        tooltipTriggerElements.forEach(trigger => {
            trigger.addEventListener('mouseenter', (e) => {
                const tooltipText = trigger.getAttribute('data-tooltip');
                this.showTooltip(e, tooltip, tooltipText);
            });
            trigger.addEventListener('mouseleave', () => this.hideTooltip(tooltip));
            trigger.addEventListener('mousemove', (e) => this.updateTooltipPosition(e, tooltip));
        });
    }
    
    showTooltip(event, tooltip, customText = null) {
        const text = customText || event.target.getAttribute('data-tooltip');
        if (!text) return;
        
        const tooltipContent = tooltip.querySelector('.tooltip-content');
        tooltipContent.textContent = text;
        
        tooltip.style.display = 'block';
        this.updateTooltipPosition(event, tooltip);
        
        // Fade in
        setTimeout(() => {
            tooltip.style.opacity = '1';
            tooltip.style.transform = 'translateY(0)';
        }, 10);
    }
    
    hideTooltip(tooltip) {
        tooltip.style.opacity = '0';
        tooltip.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            tooltip.style.display = 'none';
        }, 200);
    }
    
    updateTooltipPosition(event, tooltip) {
        const rect = tooltip.getBoundingClientRect();
        const x = event.clientX;
        const y = event.clientY;
        
        // Position tooltip above cursor by default
        let left = x - rect.width / 2;
        let top = y - rect.height - 10;
        
        // Adjust if tooltip would go off screen
        if (left < 10) left = 10;
        if (left + rect.width > window.innerWidth - 10) {
            left = window.innerWidth - rect.width - 10;
        }
        
        if (top < 10) {
            top = y + 20; // Show below cursor instead
            tooltip.className = 'tooltip bottom';
        } else {
            tooltip.className = 'tooltip top';
        }
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    // Welcome Tour System
    initializeWelcomeTour() {
        const helpButton = document.getElementById('help-tour');
        const welcomeModal = document.getElementById('welcome-modal');
        const modalClose = document.getElementById('modal-close');
        const skipTour = document.getElementById('skip-tour');
        const startTour = document.getElementById('start-tour');
        
        // Show welcome modal on first visit
        if (!localStorage.getItem('tour-completed')) {
            setTimeout(() => {
                if (welcomeModal) welcomeModal.style.display = 'flex';
            }, 1000);
        }
        
        if (helpButton) {
            helpButton.addEventListener('click', () => {
                if (welcomeModal) welcomeModal.style.display = 'flex';
            });
        }
        
        if (modalClose || skipTour) {
            [modalClose, skipTour].forEach(btn => {
                if (btn) {
                    btn.addEventListener('click', () => {
                        if (welcomeModal) welcomeModal.style.display = 'none';
                        localStorage.setItem('tour-completed', 'true');
                    });
                }
            });
        }
        
        if (startTour) {
            startTour.addEventListener('click', () => {
                if (welcomeModal) welcomeModal.style.display = 'none';
                this.startGuidedTour();
            });
        }
        
        // Close modal when clicking outside
        if (welcomeModal) {
            welcomeModal.addEventListener('click', (e) => {
                if (e.target === welcomeModal) {
                    welcomeModal.style.display = 'none';
                    localStorage.setItem('tour-completed', 'true');
                }
            });
        }
    }
    
    startGuidedTour() {
        const tourSteps = [
            {
                element: '[data-tour="file-upload"]',
                title: 'Upload Your Videos',
                description: 'Start by selecting or dragging video files here. You can upload multiple files at once.'
            },
            {
                element: '[data-tour="watermark-text"]',
                title: 'Enter Watermark Text',
                description: 'Type the text you want to embed as an invisible watermark in your videos.'
            },
            {
                element: '[data-tour="strength"]',
                title: 'Adjust Embedding Strength',
                description: 'Control the balance between invisibility and robustness of your watermark.'
            },
            {
                element: '#toggle-processing-options',
                title: 'Advanced Processing Options',
                description: 'Click here to access advanced settings for video processing and output options.'
            },
            {
                element: '.btn-primary',
                title: 'Start Processing',
                description: 'Once everything is configured, click here to begin watermarking your videos.'
            }
        ];
        
        this.currentTourStep = 0;
        this.tourSteps = tourSteps;
        this.showTourStep();
    }
    
    showTourStep() {
        const tourOverlay = document.getElementById('tour-overlay');
        const tourTitle = document.getElementById('tour-title');
        const tourDescription = document.getElementById('tour-description');
        const tourCurrent = document.getElementById('tour-current');
        const tourTotal = document.getElementById('tour-total');
        const tourPrev = document.getElementById('tour-prev');
        const tourNext = document.getElementById('tour-next');
        const tourSkip = document.getElementById('tour-skip');
        
        if (!tourOverlay || this.currentTourStep >= this.tourSteps.length) {
            this.endTour();
            return;
        }
        
        const step = this.tourSteps[this.currentTourStep];
        const element = document.querySelector(step.element);
        
        if (!element) {
            this.currentTourStep++;
            this.showTourStep();
            return;
        }
        
        // Update tour content
        if (tourTitle) tourTitle.textContent = step.title;
        if (tourDescription) tourDescription.textContent = step.description;
        if (tourCurrent) tourCurrent.textContent = this.currentTourStep + 1;
        if (tourTotal) tourTotal.textContent = this.tourSteps.length;
        
        // Position spotlight
        const rect = element.getBoundingClientRect();
        const spotlight = tourOverlay.querySelector('.tour-spotlight');
        if (spotlight) {
            spotlight.style.left = (rect.left - 10) + 'px';
            spotlight.style.top = (rect.top - 10) + 'px';
            spotlight.style.width = (rect.width + 20) + 'px';
            spotlight.style.height = (rect.height + 20) + 'px';
        }
        
        // Show overlay
        tourOverlay.style.display = 'flex';
        
        // Setup navigation
        if (tourPrev) {
            tourPrev.style.display = this.currentTourStep === 0 ? 'none' : 'block';
            tourPrev.onclick = () => this.previousTourStep();
        }
        
        if (tourNext) {
            tourNext.textContent = this.currentTourStep === this.tourSteps.length - 1 ? 'Finish' : 'Next';
            tourNext.onclick = () => this.nextTourStep();
        }
        
        if (tourSkip) {
            tourSkip.onclick = () => this.endTour();
        }
    }
    
    nextTourStep() {
        this.currentTourStep++;
        this.showTourStep();
    }
    
    previousTourStep() {
        this.currentTourStep--;
        this.showTourStep();
    }
    
    endTour() {
        const tourOverlay = document.getElementById('tour-overlay');
        if (tourOverlay) tourOverlay.style.display = 'none';
        localStorage.setItem('tour-completed', 'true');
    }

    // Character Counter
    initializeCharacterCounter() {
        const watermarkInput = document.getElementById('watermark-text');
        const charCount = document.getElementById('char-count');
        
        if (watermarkInput && charCount) {
            watermarkInput.addEventListener('input', (e) => {
                const count = e.target.value.length;
                charCount.textContent = count;
                
                // Change color based on usage - fixed logic order
                if (count > 45) {
                    charCount.style.color = 'var(--error-color)';
                } else if (count > 40) {
                    charCount.style.color = 'var(--warning-color)';
                } else {
                    charCount.style.color = 'var(--primary-color)';
                }
            });
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoWatermarkApp();
});

// Add slideOutRight animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
