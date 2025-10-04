
document.addEventListener('DOMContentLoaded', () => {
    const imageGrid = document.getElementById('image-grid');
    const selectImgDirBtn = document.getElementById('select-img-dir-btn');
    const imgDirPath = document.getElementById('img-dir-path');
    const selectTargetFolderBtn = document.getElementById('select-target-folder-btn');
    const targetFolderPath = document.getElementById('target-folder-path');
    const loading = document.getElementById('loading');
    const confirmModal = document.getElementById('confirm-modal');
    const modalText = document.getElementById('modal-text');
    const confirmBtn = document.getElementById('confirm-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const browseModal = document.getElementById('browse-modal');
    const browsePath = document.getElementById('browse-path');
    const browseList = document.getElementById('browse-list');
    const browseSelectBtn = document.getElementById('browse-select-btn');
    const browseCancelBtn = document.getElementById('browse-cancel-btn');
    const folderColorPicker = document.getElementById('folder-color-picker');
    const resetColorBtn = document.getElementById('reset-color-btn');
    const currentFolderIcon = document.getElementById('current-folder-icon');
    const currentIconImg = document.getElementById('current-icon-img');

    let selectedIconPath = null;
    let currentBrowsePath = '/';
    let browseCallback = null;
    let browseType = 'image';

    async function browse(path) {
        try {
            const response = await fetch(`/api/browse?path=${encodeURIComponent(path)}&type=${browseType}`);
            const data = await response.json();
            browsePath.textContent = data.path;
            currentBrowsePath = data.path;
            browseList.innerHTML = '';

            const parentPath = data.path.substring(0, data.path.lastIndexOf('/')) || '/';
            const parentLi = document.createElement('li');
            parentLi.textContent = '..';
            parentLi.addEventListener('click', () => {
                browse(parentPath);
            });
            browseList.appendChild(parentLi);

            data.dirs.forEach(dir => {
                const li = document.createElement('li');
                li.textContent = `[${dir}]`;
                li.addEventListener('click', () => {
                    browse(`${data.path}/${dir}`.replace('//', '/'));
                });
                browseList.appendChild(li);
            });

        } catch (error) {
            console.error('Error browsing:', error);
        }
    }

    function openBrowseModal(type, callback) {
        browseType = type;
        browseCallback = callback;
        browse(type === 'image' ? imgDirPath.textContent : targetFolderPath.textContent || '/home/herb/Desktop');
        browseModal.style.display = 'block';
    }

    function closeBrowseModal() {
        browseModal.style.display = 'none';
        browseCallback = null;
    }

    async function fetchImages(dir) {
        loading.style.display = 'block';
        imageGrid.innerHTML = '';

        try {
            const response = await fetch(`/api/images?dir=${encodeURIComponent(dir)}`);
            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.error || 'Error loading images.');
                return;
            }
            const data = await response.json();

            // Check if we should show existing folder icons instead of default folder
            const targetPath = targetFolderPath.textContent;
            let showExistingIcons = false;
            let existingIconPath = null;

            if (targetPath && dir === targetPath) {
                try {
                    const iconResponse = await fetch('/api/get-folder-icon', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ folder_path: targetPath })
                    });
                    const iconResult = await iconResponse.json();
                    if (iconResult.success) {
                        showExistingIcons = true;
                        existingIconPath = iconResult.icon_path;
                    }
                } catch (error) {
                    console.log('No existing icon found');
                }
            }

            data.images.forEach(imageName => {
                const item = document.createElement('div');
                item.className = 'grid-item';

                const folderImg = document.createElement('img');
                folderImg.alt = 'Folder background';
                folderImg.loading = 'lazy';

                // Replace default folder image if showing existing icons
                if (showExistingIcons && existingIconPath) {
                    folderImg.src = existingIconPath;
                    folderImg.className = 'folder-background existing-icon';
                } else {
                    folderImg.src = '/static/folder.svg';
                    folderImg.className = 'folder-background';

                    // Apply current color picker setting to new folder images
                    const currentColor = localStorage.getItem('currentFolderColor') || '#FFB74D';
                    folderImg.style.filter = `hue-rotate(${getHueRotation(currentColor)}deg) saturate(1.5)`;
                }

                const iconImg = document.createElement('img');
                const imagePath = `${data.image_dir}/${imageName}`;
                iconImg.src = `/images/${imageName}?dir=${encodeURIComponent(data.image_dir)}`;
                iconImg.alt = imageName;
                iconImg.className = 'icon-image';
                iconImg.loading = 'lazy';

                // Add error handling for image loading
                iconImg.onerror = function() {
                    console.warn('Failed to load image:', imagePath);
                    this.style.display = 'none';
                };

                folderImg.onerror = function() {
                    console.warn('Failed to load folder background:', this.src);
                    this.style.display = 'none';
                };

                item.appendChild(folderImg);
                item.appendChild(iconImg);
                imageGrid.appendChild(item);

                item.addEventListener('click', () => {
                    const folderPath = targetFolderPath.textContent;
                    if (!folderPath) {
                        alert('Please select a target folder.');
                        return;
                    }
                    selectedIconPath = imagePath;
                    modalText.textContent = `Set this image as the icon for "${folderPath}"?`;
                    confirmModal.style.display = 'block';
                });
            });
        } catch (error) {
            console.error('Error fetching images:', error);
        } finally {
            loading.style.display = 'none';
        }
    }

    async function setFolderIcon() {
        const folderPath = targetFolderPath.textContent;
        if (!folderPath || !selectedIconPath) return;

        try {
            const response = await fetch('/api/set-folder-icon', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    folder_path: folderPath,
                    icon_path: selectedIconPath
                })
            });

            const result = await response.json();

            if (result.success) {
                // No success message shown - just refresh the display
                // Refresh the current folder icon display
                loadCurrentFolderIcon(folderPath);
                // Refresh the grid to show the new icon as background
                fetchImages(imgDirPath.textContent);
            } else {
                // Only show error messages, not success messages
                alert(result.message || 'Failed to set folder icon');
            }

        } catch (error) {
            console.error('Error setting folder icon:', error);
            alert('An error occurred while setting the folder icon.');
        } finally {
            closeConfirmModal();
        }
    }

    function closeConfirmModal() {
        confirmModal.style.display = 'none';
        selectedIconPath = null;
    }

    function showSuccessMessage(message) {
        // Create success message element if it doesn't exist
        let successDiv = document.querySelector('.success-message');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            document.body.appendChild(successDiv);
        }

        successDiv.textContent = message;
        successDiv.classList.add('show');

        // Hide after 3 seconds
        setTimeout(() => {
            successDiv.classList.remove('show');
        }, 3000);
    }

    function updateFolderColor(color) {
        const folderImages = document.querySelectorAll('.folder-background');
        folderImages.forEach(img => {
            // Apply color filter to the SVG folder
            img.style.filter = `hue-rotate(${getHueRotation(color)}deg) saturate(1.5)`;
        });

        // Store the current color so it can be applied to new images
        localStorage.setItem('currentFolderColor', color);
    }

    function getHueRotation(hexColor) {
        // Convert hex to HSL and return hue rotation needed
        const r = parseInt(hexColor.slice(1, 3), 16) / 255;
        const g = parseInt(hexColor.slice(3, 5), 16) / 255;
        const b = parseInt(hexColor.slice(5, 7), 16) / 255;

        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h, s, l = (max + min) / 2;

        if (max === min) {
            h = s = 0;
        } else {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
                case g: h = ((b - r) / d + 2) / 6; break;
                case b: h = ((r - g) / d + 4) / 6; break;
            }
        }

        // Convert to degrees and adjust for orange base color
        return (h * 360) - 38; // 38 is approximately the hue of orange #FFB74D
    }

    async function loadCurrentFolderIcon(folderPath) {
        if (!folderPath) {
            currentFolderIcon.style.display = 'none';
            return;
        }

        try {
            // Get the current metadata::custom-icon for the folder
            const response = await fetch('/api/get-folder-icon', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ folder_path: folderPath })
            });

            const result = await response.json();

            if (result.success && result.icon_path) {
                currentIconImg.src = result.icon_path;
                currentFolderIcon.style.display = 'flex';
            } else {
                currentFolderIcon.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading folder icon:', error);
            currentFolderIcon.style.display = 'none';
        }
    }

    selectImgDirBtn.addEventListener('click', () => {
        openBrowseModal('image', (path) => {
            imgDirPath.textContent = path;
            fetchImages(path);
        });
    });

    selectTargetFolderBtn.addEventListener('click', () => {
        openBrowseModal('target', (path) => {
            targetFolderPath.textContent = path;
            loadCurrentFolderIcon(path);
            // Refresh the grid to show existing folder icon if browsing the target folder
            fetchImages(imgDirPath.textContent);
        });
    });

    browseSelectBtn.addEventListener('click', () => {
        if (browseCallback) {
            browseCallback(currentBrowsePath);
        }
        closeBrowseModal();
    });

    browseCancelBtn.addEventListener('click', closeBrowseModal);
    confirmBtn.addEventListener('click', setFolderIcon);
    cancelBtn.addEventListener('click', closeConfirmModal);

    // Color picker event listeners
    folderColorPicker.addEventListener('input', (e) => {
        updateFolderColor(e.target.value);
    });

    resetColorBtn.addEventListener('click', () => {
        folderColorPicker.value = '#FFB74D';
        updateFolderColor('#FFB74D');
        localStorage.removeItem('currentFolderColor');
    });

    window.addEventListener('beforeunload', () => {
        navigator.sendBeacon('/api/disconnect');
    });

    // Initial load - restore stored color if any
    const storedColor = localStorage.getItem('currentFolderColor');
    if (storedColor) {
        folderColorPicker.value = storedColor;
        updateFolderColor(storedColor);
    }

    fetchImages(imgDirPath.textContent);
});
