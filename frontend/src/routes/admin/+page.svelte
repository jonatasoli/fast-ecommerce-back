<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let projects = [];
	let loading = true;
	let error = null;
	let showCreateForm = false;
	let editingProject = null;

	let newProject = {
		title: '',
		slug: '',
		short_description: '',
		description: null,
		story: null,
		risks_and_challenges: null,
		main_image: '',
		video_url: '',
		category: '',
		location: '',
		start_date: new Date().toISOString().split('T')[0],
		end_date: '',
		goal_amount: 0,
		active: true,
		published: false
	};

	onMount(async () => {
		await loadProjects();
	});

	async function loadProjects() {
		try {
			loading = true;
			const token = localStorage.getItem('token');
			if (!token) {
				throw new Error('Não autenticado');
			}
			// For admin, get all projects
			projects = await api.listProjects({ published_only: false, active_only: false });
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function generateSlug() {
		newProject.slug = newProject.title
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-+|-+$/g, '');
	}

	async function createProject() {
		try {
			loading = true;
			const token = localStorage.getItem('token');
			if (!token) {
				throw new Error('Não autenticado');
			}
			// Get user_id from token (would need to decode JWT or get from API)
			const user = JSON.parse(localStorage.getItem('user') || '{}');
			newProject.user_id = user.user_id;
			await api.createProject(newProject, token);
			showCreateForm = false;
			await loadProjects();
			// Reset form
			newProject = {
				title: '',
				slug: '',
				short_description: '',
				description: null,
				story: null,
				risks_and_challenges: null,
				main_image: '',
				video_url: '',
				category: '',
				location: '',
				start_date: new Date().toISOString().split('T')[0],
				end_date: '',
				goal_amount: 0,
				active: true,
				published: false
			};
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function editProject(project) {
		editingProject = project;
		showCreateForm = true;
		newProject = { ...project };
	}
</script>

<svelte:head>
	<title>Admin - Crowdfunding</title>
</svelte:head>

<div class="container">
	<h1>Administração de Projetos</h1>

	<div class="actions">
		<button class="btn-create" on:click={() => { showCreateForm = true; editingProject = null; }}>
			+ Criar Novo Projeto
		</button>
	</div>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	{#if showCreateForm}
		<div class="modal-overlay" on:click={() => showCreateForm = false}>
			<div class="modal-content" on:click|stopPropagation>
				<h2>{editingProject ? 'Editar' : 'Criar'} Projeto</h2>
				<form on:submit|preventDefault={createProject}>
					<div class="form-group">
						<label>Título *</label>
						<input type="text" bind:value={newProject.title} on:input={generateSlug} required />
					</div>
					<div class="form-group">
						<label>Slug *</label>
						<input type="text" bind:value={newProject.slug} required />
					</div>
					<div class="form-group">
						<label>Descrição Curta</label>
						<textarea bind:value={newProject.short_description} rows="3"></textarea>
					</div>
					<div class="form-group">
						<label>Imagem Principal (URL)</label>
						<input type="url" bind:value={newProject.main_image} />
					</div>
					<div class="form-group">
						<label>Vídeo (URL)</label>
						<input type="url" bind:value={newProject.video_url} />
					</div>
					<div class="form-group">
						<label>Categoria</label>
						<input type="text" bind:value={newProject.category} />
					</div>
					<div class="form-group">
						<label>Localização</label>
						<input type="text" bind:value={newProject.location} />
					</div>
					<div class="form-row">
						<div class="form-group">
							<label>Data de Início *</label>
							<input type="date" bind:value={newProject.start_date} required />
						</div>
						<div class="form-group">
							<label>Data de Término *</label>
							<input type="date" bind:value={newProject.end_date} required />
						</div>
					</div>
					<div class="form-group">
						<label>Meta (R$) *</label>
						<input type="number" step="0.01" bind:value={newProject.goal_amount} required />
					</div>
					<div class="form-row">
						<label>
							<input type="checkbox" bind:checked={newProject.active} />
							Ativo
						</label>
						<label>
							<input type="checkbox" bind:checked={newProject.published} />
							Publicado
						</label>
					</div>
					<div class="form-actions">
						<button type="button" class="btn-cancel" on:click={() => showCreateForm = false}>
							Cancelar
						</button>
						<button type="submit" class="btn-submit" disabled={loading}>
							{loading ? 'Salvando...' : 'Salvar'}
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}

	{#if loading && !showCreateForm}
		<p>Carregando projetos...</p>
	{:else if projects.length === 0}
		<p>Nenhum projeto encontrado.</p>
	{:else}
		<div class="projects-list">
			{#each projects as project}
				<div class="project-card">
					<div class="project-header">
						<h3>{project.title}</h3>
						<div class="project-status">
							<span class="badge" class:active={project.active} class:published={project.published}>
								{project.active ? 'Ativo' : 'Inativo'} / {project.published ? 'Publicado' : 'Rascunho'}
							</span>
						</div>
					</div>
					<div class="project-info">
						<p><strong>Slug:</strong> {project.slug}</p>
						<p><strong>Meta:</strong> R$ {project.goal_amount.toFixed(2)}</p>
						<p><strong>Arrecadado:</strong> R$ {project.current_amount.toFixed(2)}</p>
						<p><strong>Apoiadores:</strong> {project.backers_count}</p>
					</div>
					<div class="project-actions">
						<a href="/project/{project.slug}" class="btn-view">Ver Projeto</a>
						<button class="btn-edit" on:click={() => editProject(project)}>Editar</button>
						<a href="/admin/project/{project.project_id}" class="btn-manage">Gerenciar</a>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	.actions {
		margin-bottom: 2rem;
	}

	.btn-create {
		padding: 0.75rem 1.5rem;
		background: #00c853;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-weight: bold;
	}

	.btn-create:hover {
		background: #00a043;
	}

	.projects-list {
		display: grid;
		gap: 1.5rem;
	}

	.project-card {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
	}

	.project-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.project-header h3 {
		margin: 0;
	}

	.badge {
		padding: 0.25rem 0.75rem;
		border-radius: 12px;
		font-size: 0.85rem;
		background: #e0e0e0;
		color: #666;
	}

	.badge.active {
		background: #c8e6c9;
		color: #2e7d32;
	}

	.badge.published {
		background: #b3e5fc;
		color: #0277bd;
	}

	.project-info {
		margin: 1rem 0;
	}

	.project-info p {
		margin: 0.5rem 0;
	}

	.project-actions {
		display: flex;
		gap: 1rem;
		margin-top: 1rem;
	}

	.btn-view,
	.btn-edit,
	.btn-manage {
		padding: 0.5rem 1rem;
		border-radius: 4px;
		text-decoration: none;
		font-size: 0.9rem;
		cursor: pointer;
		border: none;
	}

	.btn-view {
		background: #2196f3;
		color: white;
	}

	.btn-edit {
		background: #ff9800;
		color: white;
	}

	.btn-manage {
		background: #9c27b0;
		color: white;
	}

	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 8px;
		padding: 2rem;
		max-width: 600px;
		width: 90%;
		max-height: 90vh;
		overflow-y: auto;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: bold;
	}

	.form-group input,
	.form-group textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		font-size: 1rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		margin-top: 1.5rem;
	}

	.btn-cancel,
	.btn-submit {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-weight: bold;
	}

	.btn-cancel {
		background: #e0e0e0;
		color: #333;
	}

	.btn-submit {
		background: #00c853;
		color: white;
	}

	.error {
		background: #ffebee;
		color: #d32f2f;
		padding: 1rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}
</style>
