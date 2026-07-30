document.addEventListener('DOMContentLoaded', function() {
    const similarSearchInput = document.getElementById('similar-search');
    const similarResultsContainer = document.getElementById('similar-results');
    const selectedSimilarList = document.getElementById('selected-similar-list');
    const similaresIdsInput = document.getElementById('similares_ids');
    const loader = document.getElementById('similar-search-loader');

    // Obtém URLs e IDs dos atributos do wrapper #page-root (se existir) ou do body como fallback
    const pageRoot = document.getElementById('page-root');
    const datasetSource = pageRoot ? pageRoot.dataset : document.body.dataset;
    const similarSearchUrl = datasetSource.similarSearchUrl;
    const produtoId = datasetSource.productId;

    if (!similarSearchInput || !similarSearchUrl) {
        return; // Sai se os elementos essenciais não existirem
    }

    let searchDebounceTimer;

    // Função para atualizar a lista de IDs de similares
    function updateSimilarIds() {
        const ids = Array.from(selectedSimilarList.children).map(item => item.dataset.id);
        similaresIdsInput.value = ids.join(',');
    }

    // Função para adicionar um item à lista de selecionados
    function addSimilar(item) {
        // Verifica se o item já foi adicionado
        if (document.querySelector(`.selected-similar-item[data-id="${item.id}"]`)) {
            return;
        }

        const div = document.createElement('div');
        div.classList.add('selected-similar-item');
        div.dataset.id = item.id;
        div.innerHTML = `<span>${item.codigo} - ${item.nome}</span><button type="button" class="remove-similar-btn" title="Remover">×</button>`;
        selectedSimilarList.appendChild(div);
        updateSimilarIds();
    }

    // Listener para o input de busca de similares
    similarSearchInput.addEventListener('input', function() {
        clearTimeout(searchDebounceTimer);
        const termo = this.value.trim();

        if (termo.length < 2) {
            similarResultsContainer.innerHTML = '';
            similarResultsContainer.style.display = 'none';
            return;
        }

        if (loader) loader.style.display = 'block'; // Mostra o loader

        searchDebounceTimer = setTimeout(() => {
            const url = `${similarSearchUrl}?q=${encodeURIComponent(termo)}&exclude_id=${produtoId || ''}`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    similarResultsContainer.innerHTML = '';
                    if (data.items && data.items.length > 0) {
                        data.items.forEach(item => {
                            const div = document.createElement('div');
                            div.classList.add('similar-result-item');
                            div.textContent = `${item.codigo} - ${item.nome}`;
                            div.addEventListener('click', () => {
                                addSimilar(item);
                                similarSearchInput.value = '';
                                similarResultsContainer.style.display = 'none';
                            });
                            similarResultsContainer.appendChild(div);
                        });
                        similarResultsContainer.style.display = 'block';
                    } else {
                        similarResultsContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Erro ao buscar peças similares:', error);
                    similarResultsContainer.style.display = 'none';
                })
                .finally(() => {
                    if (loader) loader.style.display = 'none'; // Esconde o loader
                });
        }, 400); // Aguarda 400ms
    });

    // Esconde os resultados se clicar fora
    document.addEventListener('click', function(e) {
        if (!similarSearchInput.contains(e.target)) {
            similarResultsContainer.style.display = 'none';
        }
    });

    // Delegação de evento para remover itens selecionados
    selectedSimilarList.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('remove-similar-btn')) {
            e.target.closest('.selected-similar-item').remove();
            updateSimilarIds();
        }
    });

    // Preview de novas imagens
    const imagensInput = document.getElementById('imagens');
    const previewContainer = document.getElementById('new-image-preview-container');
    if (imagensInput && previewContainer) {
        imagensInput.addEventListener('change', function(event) {
            previewContainer.innerHTML = ''; // Limpa previews antigos
            for (const file of event.target.files) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.width = '100px';
                    img.style.height = '100px';
                    img.style.objectFit = 'cover';
                    img.style.borderRadius = '4px';
                    previewContainer.appendChild(img);
                }
                reader.readAsDataURL(file);
            }
        });
    }
});